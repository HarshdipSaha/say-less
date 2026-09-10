"""One booking conversation. Bind, plan, speak, or commit."""
from dataclasses import dataclass, field as dc_field

from .binder import BinderCache, bind
from .evidence import TurnEvidence
from .keyterms import prospective_terms, reactive_terms
from .matcher import match
from .moves import MoveKind, RepairMove, readback
from .planner import (TURN_TROUBLE_THRESHOLD, RepairState,
                      plan_after_rejection, plan_repair)
from .schema import ROOT, BOOKING_SCHEMA, FieldSpec

# The live demo must not append to the committed reproducibility artifact.
DEMO_BINDER_CACHE = ROOT / "corpus" / "demo_binder_cache.json"

FIELD_ORDER = ("service", "day", "time", "surname")


# Words that carry no field value, so that "no, it's Friday" reduces to "friday".
FILLER = {"no", "nope", "nah", "not", "yes", "yeah", "yep", "it", "its", "it's",
          "i", "said", "say", "was", "is", "the", "a", "an", "please", "thats",
          "that's", "that", "my", "name", "um", "uh", "actually", "sorry"}

# Ordinary English words that are also common surnames. Public surname frequency
# lists are full of them, so without this a caller saying "no, that was long"
# gets booked as Mr Long -- on the one field marked consequential.
#
# The cost is one extra turn, not a spelling ordeal: this gates only the
# same-turn shortcut, so a caller actually named Green gets a "Which last name?"
# and then binds normally through the binder on the next turn.
SURNAME_STOPWORDS = frozenset({
    "long", "green", "price", "cook", "bell", "wood", "west", "east", "north",
    "south", "king", "young", "day", "hill", "brown", "white", "black", "gray",
    "grey", "short", "small", "little", "best", "rich", "wright", "right",
    "bill", "will", "mark", "rose", "field", "fields", "stone", "park",
    "church", "love", "hall", "case", "cross", "pope", "bishop", "baker",
    "cash", "camp", "post", "bond", "fox", "snow", "reed", "ward", "knight",
    "grant", "ford", "hunt", "mason", "close", "guess", "different",
})

# The schema's own vocabulary, plus those. A caller saying "the day" is naming a
# field, not a person.
RESERVED = (frozenset({n.lower() for n in BOOKING_SCHEMA})
            | frozenset({s.label.lower() for s in BOOKING_SCHEMA.values()})
            | SURNAME_STOPWORDS)


def named_value(said: str, spec: FieldSpec,
                reserved: frozenset[str] = frozenset()) -> str | None:
    """The value the caller actually spoke, if the whole utterance is that value.

    Substring matching is not safe here. Common surname lists contain Day, Green,
    King, Price, Cook, Bell, Wood, West and Long, so "no that's the wrong day"
    would otherwise book an appointment for a Mr Day -- on the one field marked
    consequential. Requiring the utterance to reduce to exactly one value, after
    dropping filler, keeps "no, Friday" working and rejects the rest.

    `reserved` holds the schema's own field names and labels plus common
    surname-shaped English words, because "no, I said the day" reduces to
    "day", which is the name of a field rather than the surname of a caller.
    """
    tokens = [t.strip(".,?!") for t in said.lower().split()]
    content = [t for t in tokens if t and t not in FILLER]
    if not content:
        return None
    joined = " ".join(content)
    if joined in reserved:
        return None
    return next((v for v in spec.values if v.lower() == joined), None)


@dataclass
class BookingSession:
    schema: dict[str, FieldSpec] = dc_field(default_factory=lambda: dict(BOOKING_SCHEMA))
    values: dict[str, str] = dc_field(default_factory=dict)
    state: RepairState = dc_field(default_factory=RepairState)
    cache: BinderCache = dc_field(
        default_factory=lambda: BinderCache(DEMO_BINDER_CACHE))
    pending: RepairMove | None = None
    awaiting_readback: bool = False
    done: bool = False

    def expected_fields(self) -> list[str]:
        return [f for f in FIELD_ORDER if f not in self.values]

    def opening_keyterms(self) -> list[str]:
        return prospective_terms(self.expected_fields(), self.schema)

    def handle_turn(self, turn: TurnEvidence) -> tuple[str, list[str]]:
        """Return (what the agent says, keyterms to push next)."""
        self.state.new_turn()
        said = turn.transcript.strip().lower()

        if self.awaiting_readback:
            self.awaiting_readback = False
            if said.startswith("yes"):
                self.done = True
                return "Booked. See you then.", []
            self.values.clear()
            return "Let's try that again. Which service?", prospective_terms(
                ["service"], self.schema)

        if self.pending and self.pending.candidates:
            answered = self._answer_to_pending(said)
            if answered is not None:
                return answered

        fields = bind(turn.transcript, [w.text for w in turn.words],
                      self.schema, self.cache)
        move = plan_repair(turn, fields, self.schema, self.state)

        # Keep every field heard cleanly, even when another field in the same
        # turn needs repair. Otherwise "a haircut on chewsday" repairs the day
        # and then asks for the service again -- making the caller re-say a word
        # the agent got right, which is the exact cost this project reduces.
        self._commit_clean(fields, turn)

        if move is not None:
            self.state.record(move)
            if move.kind is MoveKind.ESCALATE:
                self.done = True
                self.pending = None
                return move.utterance, []
            self.pending = move
            return move.utterance, reactive_terms(move)

        self.pending = None
        return self._advance()

    def _commit_clean(self, fields, turn: TurnEvidence) -> None:
        """Accept bindings that are in-set and confident. Mirrors the planner's
        accept condition, so it can never commit a value the planner is about to
        ask about.

        Deliberately skipped when the turn as a whole is suspect: if the planner
        treated the turn-level confidence as trouble, nothing from that turn is
        trustworthy enough to keep.
        """
        if turn.end_of_turn_confidence < TURN_TROUBLE_THRESHOLD:
            return
        for bf in fields:
            spec = self.schema.get(bf.field)
            if spec is None or bf.field in self.values:
                continue
            m = match(bf.heard_value, spec.values)
            if m.in_set and turn.min_confidence(bf.word_indices) >= spec.confidence_threshold:
                self.values[bf.field] = next(v for v in spec.values if v.lower() == m.heard)

    def _answer_to_pending(self, said: str) -> tuple[str, list[str]] | None:
        """Resolve an answer to the offer currently on the table.

        Order matters. A caller who says "no, Friday" has supplied the answer,
        and the value they named beats the rejection they led with.
        """
        move, field = self.pending, self.pending.field
        spec = self.schema[field]

        # 1. The caller named a value from this field's set. Take it.
        named = named_value(said, spec, RESERVED)
        if named:
            self.values[field] = named
            self.pending = None
            return self._advance()

        # 2. Bare confirmation of the candidate on the table.
        if said.startswith("yes") and move.candidates:
            self.values[field] = move.candidates[0]
            self.pending = None
            return self._advance()

        # 3. Rejection. Re-plan through the planner so that every cap that
        #    governs a first repair governs this one too. Without this the agent
        #    would offer a new name on every "no" until the value set ran out --
        #    122 consecutive offers on the surname field, never escalating.
        if said.startswith(("no", "nope", "nah")):
            nxt = plan_after_rejection(field, spec, self.state)
            self.state.record(nxt)
            if nxt.kind is MoveKind.ESCALATE:
                self.done = True
                self.pending = None
                return nxt.utterance, []
            self.pending = nxt
            return nxt.utterance, reactive_terms(nxt)

        return None

    def _advance(self) -> tuple[str, list[str]]:
        missing = self.expected_fields()
        if missing:
            nxt = missing[0]
            return (f"And the {self.schema[nxt].label}?",
                    prospective_terms([nxt] + missing[1:], self.schema))
        summary = (f"{self.values['service']} on {self.values['day']} at "
                   f"{self.values['time']} for {self.values['surname']}")
        self.awaiting_readback = True
        return readback(summary).utterance, ["yes", "no"]

    def book(self) -> dict:
        """The single fake tool. Fires only after the readback is confirmed."""
        return {"status": "booked", **self.values}
