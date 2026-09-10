"""Gate measurement. Streams fixture audio through Universal-Streaming and reports
whether a misheard bounded value is recoverable from the field's value set.

Standalone on purpose: it must run before any project module exists.
"""
import asyncio, difflib, json, os, statistics, sys, wave
from pathlib import Path

import websockets
from dotenv import load_dotenv
from metaphone import doublemetaphone
from rapidfuzz import fuzz

load_dotenv()
API_KEY = os.environ["ASSEMBLYAI_API_KEY"]
URL = ("wss://streaming.assemblyai.com/v3/ws"
       "?sample_rate=16000&encoding=pcm_s16le&format_turns=false")
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "out"


def phonetic_score(heard: str, candidate: str) -> float:
    hc = [c for c in doublemetaphone(heard) if c]
    cc = [c for c in doublemetaphone(candidate) if c]
    code = max((fuzz.ratio(a, b) for a in hc for b in cc), default=0) / 100
    literal = fuzz.ratio(heard.lower(), candidate.lower()) / 100
    return round(0.7 * code + 0.3 * literal, 4)


async def _transcribe_once(path: Path) -> list[dict]:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == 16000, f"{path} is not 16 kHz"
        assert w.getnchannels() == 1, f"{path} is not mono"
        assert w.getsampwidth() == 2, f"{path} is not 16-bit"
        pcm = w.readframes(w.getnframes())

    turns: list[dict] = []
    async with websockets.connect(URL, additional_headers={"Authorization": API_KEY}) as ws:
        async def send():
            step = int(16000 * 0.05) * 2          # 50 ms of 16-bit mono
            for i in range(0, len(pcm), step):
                await ws.send(pcm[i:i + step])
                await asyncio.sleep(0.05)
            await ws.send(json.dumps({"type": "Terminate"}))

        async def recv():
            async for raw in ws:
                if isinstance(raw, bytes):
                    continue
                msg = json.loads(raw)
                if msg.get("type") == "Turn":
                    turns.append(msg)
                elif msg.get("type") == "Termination":
                    return

        await asyncio.gather(send(), recv())
    return turns


async def transcribe(path: Path) -> list[dict]:
    """Retries on transient close (e.g. a concurrent-session limit briefly
    tripped by back-to-back connections) with backoff and a cool-down pause."""
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            return await _transcribe_once(path)
        except websockets.exceptions.ConnectionClosedError as e:
            last_exc = e
            wait = 2 * (attempt + 1)
            print(f"  ({path.name}: connection closed, retry {attempt + 1} in {wait}s: {e})")
            await asyncio.sleep(wait)
    raise last_exc


def aligned_slot(hyp_words: list[str], ref_words: list[str],
                 span: tuple[int, int]) -> tuple[str, bool]:
    """Return the hypothesis text aligned to the reference slot span.

    Position-based, not similarity-based, so the estimator is independent of the
    quantity being measured. Returns (text, aligned_ok).
    """
    lo, hi = span
    sm = difflib.SequenceMatcher(
        a=[w.lower() for w in ref_words], b=[w.lower() for w in hyp_words])
    picked: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if i2 <= lo or i1 >= hi:
            continue
        if tag == "equal":
            off_lo, off_hi = max(lo, i1) - i1, min(hi, i2) - i1
            picked.extend(hyp_words[j1 + off_lo: j1 + off_hi])
        else:
            picked.extend(hyp_words[j1:j2])      # replace/insert/delete region
    if picked:
        return " ".join(picked), True
    # Alignment produced nothing; fall back and flag it so the run can be judged.
    return "", False


def clean(s: str) -> str:
    return s.strip().strip(".,?!").lower()


async def main() -> int:
    manifest = json.loads((ROOT / "corpus" / "manifest.json").read_text())
    fields = dict(manifest["fields"])
    surnames_file = ROOT / "corpus" / "surnames.txt"
    if surnames_file.exists():
        fields["surname"] = [l.strip() for l in surnames_file.read_text().splitlines() if l.strip()]
    OUT.mkdir(exist_ok=True)

    rows, correct_confs, wrong_confs, unaligned = [], [], [], 0
    for item in manifest["items"]:
        await asyncio.sleep(1.0)          # let the prior session fully close server-side
        values = fields[item["field"]]
        turns = await transcribe(ROOT / "corpus" / item["take1"])
        (OUT / f"{item['id']}_frames.json").write_text(json.dumps(turns, indent=2))

        finals = [t for t in turns if t.get("end_of_turn")]
        if not finals:
            print(f"{item['id']}: NO FINAL TURN"); continue
        final = finals[-1]
        hyp = [w["text"] for w in (final.get("words") or [])]
        if not hyp:
            print(f"{item['id']}: NO WORDS"); continue

        heard_raw, ok = aligned_slot(hyp, item["sentence"].split(), tuple(item["slot_span"]))
        if not ok:
            unaligned += 1
            print(f"{item['id']}: ALIGNMENT FAILED"); continue

        heard = clean(heard_raw)
        truth = clean(item["truth"])
        is_wrong = heard != truth

        # Confidence of the slot region = min over the words that produced it.
        span_texts = {clean(t) for t in heard_raw.split()}
        confs = [float(w["confidence"]) for w in final["words"] if clean(w["text"]) in span_texts]
        conf = min(confs) if confs else 1.0

        in_set = heard in {clean(v) for v in values}
        ranked = sorted(((v, phonetic_score(heard, v)) for v in values),
                        key=lambda p: p[1], reverse=True)
        rank = next((i + 1 for i, (v, _) in enumerate(ranked) if clean(v) == truth), None)

        (wrong_confs if is_wrong else correct_confs).append(conf)
        rows.append({"id": item["id"], "field": item["field"],
                     "truth": item["truth"], "heard": heard,
                     "wrong": is_wrong, "conf": round(conf, 3), "in_set": in_set,
                     "truth_rank": rank,
                     "top3": [(v, round(s, 3)) for v, s in ranked[:3]]})
        print(f"{item['id']:<10} truth={item['truth']:<16} heard={heard:<18} "
              f"wrong={is_wrong} conf={conf:.2f} in_set={in_set} rank={rank}")

    (OUT / "gate_rows.json").write_text(json.dumps(rows, indent=2))

    wrong = [r for r in rows if r["wrong"]]
    print("\n" + "=" * 74)
    print(f"scored:                        {len(rows)}   (alignment failures: {unaligned})")
    print(f"misheard slot values:          {len(wrong)}")
    if wrong:
        oos = sum(1 for r in wrong if not r["in_set"])
        r12 = sum(1 for r in wrong if r["truth_rank"] in (1, 2))
        print(f"  fell outside the value set:  {oos}/{len(wrong)} ({oos/len(wrong):.0%})")
        print(f"  truth at phonetic rank 1-2:  {r12}/{len(wrong)} ({r12/len(wrong):.0%})"
              "   <-- GO threshold is 60%")
    if correct_confs and wrong_confs:
        mc, mw = statistics.mean(correct_confs), statistics.mean(wrong_confs)
        print(f"mean confidence, correct:      {mc:.3f}")
        print(f"mean confidence, misheard:     {mw:.3f}")
        print(f"  confidence separates:        {mw < mc - 0.05}")
    print("=" * 74)
    if unaligned > 2:
        print("WARNING: more than two alignment failures. Fix slot_span before deciding.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
