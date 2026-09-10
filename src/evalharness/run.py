"""Replay the corpus through the baseline and through Say Less and print the table.

Both arms share every component except which planner is called. Transcriptions and
binder responses are cached, so a clean checkout reproduces the published numbers.
"""
import argparse, asyncio, json
from pathlib import Path

from dotenv import load_dotenv

from sayless.baseline import plan_repair_baseline
from sayless.binder import BinderCache, bind
from sayless.decisionlog import DecisionLog
from sayless.keyterms import reactive_terms
from sayless.matcher import match
from sayless.planner import RepairState, plan_after_rejection, plan_repair
from sayless.schema import BOOKING_SCHEMA
from sayless.stream import TranscriptCache, transcribe_file
from evalharness.metrics import RunRecord, aggregate, table
from evalharness.simulator import respond

ROOT = Path(__file__).resolve().parents[2]
MAX_TURNS = 5


class Transcriber:
    """Streams each (audio, keyterms) condition once and persists the result.

    The persistence is not an optimisation. Without it the published table
    cannot be regenerated from a clean checkout, which is spec story 22.
    """

    def __init__(self, path: Path, offline: bool = False) -> None:
        self.cache = TranscriptCache(path)
        self.offline = offline
        self.misses = 0

    async def get(self, audio: Path, keyterms: list[str] | None):
        hit, turn = self.cache.get(audio, keyterms)
        if hit:
            return turn
        self.misses += 1
        if self.offline:
            # Named failure beats a websocket error on an empty API key, which
            # is what a clean-clone reproduction attempt would otherwise hit.
            raise RuntimeError(
                f"condition was never cached: {audio.name} "
                f"keyterms={sorted(keyterms or [])}. Re-run online, then commit "
                f"{self.cache.path.name}.")
        turn = await transcribe_file(audio, keyterms)
        self.cache.put(audio, keyterms, turn)
        self.cache.save()          # incremental: a hiccup on item 14 costs one item
        return turn

    def save(self) -> None:
        self.cache.save()


async def run_item(item, planner, arm, tx, bcache, log, reactive: bool,
                   offline: bool = False) -> RunRecord:
    spec = BOOKING_SCHEMA[item["field"]]
    truth = item["truth"]
    answer_words = len(truth.split())
    sentence_words = len(item["sentence"].split())

    state = RepairState()
    audio = ROOT / "corpus" / item["take1"]
    keyterms: list[str] | None = None
    repair_words = turns = 0
    committed, in_set, confident, escalated = None, False, False, False
    pending_offer = None

    for _ in range(MAX_TURNS):
        turns += 1
        turn = await tx.get(audio, keyterms)
        if turn is None:
            break

        if pending_offer is not None:
            # The caller rejected an offer. Follow the shipped ladder, exactly as
            # BookingSession does, instead of re-planning the word "no" from
            # scratch. Without this the harness measures a policy the demo does
            # not use: a rejected offer would fall through to an open request and
            # cost the caller the whole sentence again, making the seam look
            # worse than the baseline on the one branch it exists to improve.
            # The baseline never reaches here because it never names a candidate.
            fields = []
            move = plan_after_rejection(item["field"], spec, state)
            pending_offer = None
        else:
            fields = bind(turn.transcript, [w.text for w in turn.words],
                          BOOKING_SCHEMA, bcache, offline=offline)
            move = planner(turn, fields, BOOKING_SCHEMA, state)
        log.write(arm, item["id"], turn, fields, move)

        if move is None:
            bf = next((b for b in fields if b.field == item["field"]), None)
            if bf:
                m = match(bf.heard_value, spec.values)
                in_set = m.in_set
                confident = turn.min_confidence(bf.word_indices) >= spec.confidence_threshold
                committed = (next(v for v in spec.values if v.lower() == m.heard)
                             if in_set else bf.heard_value)
            break

        state.record(move)
        state.new_turn()
        reply = respond(move, truth, answer_words, sentence_words)
        repair_words += reply.words

        if reply.terminal:
            escalated = True
            break
        if reply.accepted:
            committed = reply.value or committed
            break

        pending_offer = move if move.candidates else None
        keyterms = reactive_terms(move, enabled=reactive) or None
        audio = ROOT / "corpus" / (
            item["take2"] if reply.audio == "take2"
            else item["answer"] if reply.audio == "answer"
            else f"audio/{reply.audio}.wav")

    return RunRecord(item["id"], item["field"], truth, committed, turns,
                     repair_words, in_set, confident, escalated)


async def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="corpus/manifest.json")
    ap.add_argument("--out", default="eval_results.json")
    ap.add_argument("--no-reactive-keyterms", action="store_true",
                    help="disable the post-repair keyterm push, to measure its effect")
    ap.add_argument("--offline", action="store_true",
                    help="fail loudly on a cache miss instead of calling the API")
    args = ap.parse_args()
    reactive = not args.no_reactive_keyterms

    items = json.loads((ROOT / args.manifest).read_text())["items"]
    tx = Transcriber(ROOT / "corpus" / "transcript_cache.json", offline=args.offline)
    bcache = BinderCache()
    # Each run gets its own log, or the second run of Step 6 wipes the first.
    log = DecisionLog(ROOT / f"eval_decisions_{Path(args.out).stem}.jsonl")

    base = []
    for i in items:
        base.append(await run_item(i, plan_repair_baseline, "baseline", tx, bcache, log,
                                   reactive, args.offline))
        print(f"  baseline {i['id']} done (cache misses so far: {tx.misses})")
    ours = []
    for i in items:
        ours.append(await run_item(i, plan_repair, "sayless", tx, bcache, log,
                                   reactive, args.offline))
        print(f"  sayless  {i['id']} done (cache misses so far: {tx.misses})")
    tx.save()
    bcache.save()

    b, s = aggregate(base), aggregate(ours)
    print(table(b, s))
    print(f"\nreactive keyterms: {'on' if reactive else 'off'}")
    print(f"transcription cache misses (0 means fully reproduced offline): {tx.misses}")
    (ROOT / args.out).write_text(json.dumps(
        {"reactive_keyterms": reactive, "baseline": b, "sayless": s,
         "records": {"baseline": [r.__dict__ for r in base],
                     "sayless": [r.__dict__ for r in ours]}}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
