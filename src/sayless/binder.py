"""Binds parts of a turn to schema fields, with character spans so that per-word
evidence can be attached to the field it produced.

Uses a plain chat completion returning JSON rather than tool calling, because the
gateway's tool-call semantics are unverified and not worth an evening.
"""
import json
import os
from pathlib import Path

from openai import OpenAI

from .evidence import BoundField
from .schema import ROOT, FieldSpec

MODEL = os.environ.get("SAYLESS_MODEL", "qwen3.5-4b-32k-fast")
CACHE_PATH = ROOT / "corpus" / "binder_cache.json"
_client: OpenAI | None = None

# One-line hints for the model, since a bare field name ("day") is too vague on
# its own for a small model to reliably infer what to extract. Verified: the
# original bare-name prompt returned {"bindings":[]} for plain sentences like
# "Can I book a slot for Tuesday, please?" and "I would like to come in on
# Monday morning." -- every single real gate day sentence, meaning the
# evaluation harness measured nothing but escalations until this was found and
# fixed. Adding these descriptions was enough on its own to recover all of them.
FIELD_DESCRIPTIONS = {
    "day": "day of the week the caller wants (e.g. Monday, Tuesday)",
    "time": "time of day the caller wants",
    "service": "the service the caller is booking (e.g. haircut, beard trim)",
    "surname": "the caller's last name / family name",
}


class BinderCache:
    """Transcript -> binder payload. Committed, so evaluations reproduce offline."""

    def __init__(self, path: Path = CACHE_PATH) -> None:
        self.path = Path(path)
        self.data: dict[str, dict] = {}
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    def get(self, transcript: str) -> dict | None:
        return self.data.get(transcript.strip().lower())

    def put(self, transcript: str, payload: dict) -> None:
        self.data[transcript.strip().lower()] = payload

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True))


def client() -> OpenAI:
    global _client
    if _client is None:
        # An explicit timeout matters here: an unbounded call was observed to
        # hang rather than error during development, which is unacceptable in
        # a harness that makes many sequential binder calls.
        _client = OpenAI(base_url="https://llm-gateway.assemblyai.com/v1",
                         api_key=os.environ["ASSEMBLYAI_API_KEY"],
                         timeout=25.0, max_retries=2)
    return _client


# Paired examples, one clean and one garbled, for each field found to need
# them empirically -- not speculatively for all four. A single clean example
# was tried first for "day" and fixed recall on phrasings like "Let's do
# Wednesday..." / "...move it to Thursday instead" -- but it also anchored the
# model toward what a "day" value is supposed to look like strongly enough
# that a genuinely misheard value ("chewsday") got silently RECLASSIFIED to
# the "service" field instead of staying under "day". That is a worse failure
# than a missed binding: it breaks the one behaviour the whole project depends
# on. Each garbled-preserved example exists specifically to counteract that
# for its field. The same clean-only failure was independently observed for
# "service" ("I would like a beard trim" and "just a haircut today thanks"
# both returned empty bindings with descriptions alone), so it gets the same
# pair. "surname" and "time" were not observed to need this in testing and are
# left without examples rather than adding untested prompt surface area.
_BINDER_EXAMPLES = (
    'Examples:\n'
    'utterance "Lets book Friday please" -> '
    '{"bindings":[{"field":"day","value":"Friday","start":11,"end":17}]}\n'
    'utterance "can I book a chewsday appointment" -> '
    '{"bindings":[{"field":"day","value":"chewsday","start":13,"end":21}]} '
    '(garbled but still the day slot -- copy it exactly, do not correct or reassign it)\n'
    'utterance "I would like a haircut" -> '
    '{"bindings":[{"field":"service","value":"haircut","start":15,"end":22}]}\n'
    'utterance "can I get a hairkut please" -> '
    '{"bindings":[{"field":"service","value":"hairkut","start":11,"end":18}]} '
    '(garbled but still the service slot -- copy it exactly)'
)


def _prompt(transcript: str, schema: dict[str, FieldSpec]) -> str:
    fields = "\n".join(
        f"- {name}: {FIELD_DESCRIPTIONS.get(name, name)}" for name in schema)
    return (
        "Extract booking details from a caller's utterance.\n"
        f"Fields (name: description):\n{fields}\n"
        f"{_BINDER_EXAMPLES}\n"
        'Return ONLY JSON: {"bindings":[{"field":..,"value":..,'
        '"start":<char index>,"end":<char index>}]}\n'
        "Copy the value EXACTLY as it appears, even if misspelled or nonsensical. "
        "Never correct it. Never invent a value that was not spoken.\n"
        f"Utterance: {transcript}"
    )


def _word_spans(transcript: str, words: list[str]) -> list[tuple[int, int]]:
    spans, cursor, low = [], 0, transcript.lower()
    for w in words:
        i = low.find(w.lower(), cursor)
        if i < 0:
            spans.append((-1, -1))
            continue
        spans.append((i, i + len(w)))
        cursor = i + len(w)
    return spans


def parse_binder_response(payload: dict, transcript: str, words: list[str],
                          schema: dict[str, FieldSpec] | None = None) -> list[BoundField]:
    from .schema import BOOKING_SCHEMA
    schema = schema if schema is not None else BOOKING_SCHEMA
    spans = _word_spans(transcript, words)
    out: list[BoundField] = []
    for b in payload.get("bindings", []):
        if b.get("field") not in schema:
            continue
        start, end = int(b.get("start", -1)), int(b.get("end", -1))
        idx = tuple(i for i, (s, e) in enumerate(spans)
                    if s >= 0 and s < end and e > start)
        if not idx:
            continue
        out.append(BoundField(b["field"], str(b.get("value", "")).strip(), idx))
    return out


def bind(transcript: str, words: list[str], schema: dict[str, FieldSpec],
         cache: BinderCache | None = None,
         offline: bool = False) -> list[BoundField]:
    payload = cache.get(transcript) if cache else None
    if payload is None:
        if offline:
            # Same reason as the transcript cache: a named error beats an opaque
            # auth failure when someone tries to reproduce with no API key.
            raise RuntimeError(f"binding was never cached: {transcript!r}. "
                               "Re-run online, then commit binder_cache.json.")
        resp = client().chat.completions.create(
            model=MODEL, temperature=0,
            messages=[{"role": "user", "content": _prompt(transcript, schema)}])
        text = resp.choices[0].message.content or "{}"
        text = text[text.find("{"): text.rfind("}") + 1] or "{}"
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {}
        if cache:
            cache.put(transcript, payload)
            cache.save()           # incremental, so a late crash costs one item
    return parse_binder_response(payload, transcript, words, schema)
