"""Declarative field schema. A bounded field is a name plus a list of allowed values."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

KEYTERM_MAX_COUNT = 100
KEYTERM_MAX_LEN = 50

# Gate result (docs/STATUS.md, 2026-09-10): rank recovery 3/3 (100%), but
# confidence did NOT separate correct from misheard tokens (misheard mean
# confidence 0.992 was higher than correct mean confidence 0.967). Decision:
# Go, confidence-independent. Set to 0.0 so the trigger is set membership
# alone. baseline.py reads the same value, so the arms never diverge here.
CONFIDENCE_THRESHOLD = 0.0

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str                      # spoken form used in "Which {label}?"
    values: tuple[str, ...]
    consequential: bool = False
    confidence_threshold: float = CONFIDENCE_THRESHOLD
    # A large value set makes some member score well against almost anything, so
    # the bar for naming a candidate out loud rises with the size of the set.
    strong_threshold: float = 0.65

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError(f"field {self.name!r} has no allowed values")

    def contains(self, heard: str) -> bool:
        return heard.strip().lower() in {v.lower() for v in self.values}

    def keyterms(self) -> tuple[str, ...]:
        return tuple(v[:KEYTERM_MAX_LEN] for v in self.values[:KEYTERM_MAX_COUNT])


@lru_cache(maxsize=1)
def load_surnames() -> tuple[str, ...]:
    path = ROOT / "corpus" / "surnames.txt"
    return tuple(l.strip() for l in path.read_text().splitlines() if l.strip())


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
TIMES = ("nine am", "ten am", "eleven am", "twelve noon", "one pm", "two pm",
         "three pm", "four pm", "five pm", "six pm")
SERVICES = ("haircut", "beard trim", "hot towel shave", "colour", "consultation",
            "head massage", "kids cut", "fringe trim", "blow dry", "styling")

BOOKING_SCHEMA: dict[str, FieldSpec] = {
    "day": FieldSpec("day", "day", DAYS),
    "time": FieldSpec("time", "time", TIMES),
    "service": FieldSpec("service", "service", SERVICES),
    # A set this large produces a plausible-looking match for almost any input,
    # which would put a confidently wrong name in the agent's mouth on the one
    # consequential field. 0.80 is a starting value; Task 4 Step 5 re-measures it
    # against the surname list actually shipped, because the distribution moves
    # with the list.
    "surname": FieldSpec("surname", "last name", load_surnames(),
                         consequential=True, strong_threshold=0.80),
}
