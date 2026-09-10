"""The repair moves, ordered by how much they narrow the problem.

Four of them correspond to the repair-initiation types documented as universal
across languages: restricted offer, restricted request and open request, with
the two-way offer a bounded variant of the restricted offer. ESCALATE and
READBACK are not repair initiations; they bound the interaction.
"""
from dataclasses import dataclass
from enum import Enum


class MoveKind(Enum):
    ESCALATE = ("escalate", -1)
    OPEN_REQUEST = ("open_request", 0)
    RESTRICTED_REQUEST = ("restricted_request", 1)
    TWO_WAY_OFFER = ("two_way_offer", 2)
    RESTRICTED_OFFER = ("restricted_offer", 3)
    READBACK = ("readback", 4)

    def __init__(self, label: str, specificity: int) -> None:
        self.label = label
        self.specificity = specificity


@dataclass(frozen=True)
class RepairMove:
    kind: MoveKind
    field: str | None
    candidates: tuple[str, ...]
    utterance: str
    terminal: bool = False


def restricted_offer(field: str, candidate: str) -> RepairMove:
    return RepairMove(MoveKind.RESTRICTED_OFFER, field, (candidate,), f"{candidate}?")


def two_way_offer(field: str, first: str, second: str) -> RepairMove:
    return RepairMove(MoveKind.TWO_WAY_OFFER, field, (first, second),
                      f"{first} or {second}?")


def restricted_request(field: str, label: str) -> RepairMove:
    return RepairMove(MoveKind.RESTRICTED_REQUEST, field, (), f"Which {label}?")


def open_request() -> RepairMove:
    return RepairMove(MoveKind.OPEN_REQUEST, None, (),
                      "Sorry, could you say that again?")


def escalate() -> RepairMove:
    return RepairMove(MoveKind.ESCALATE, None, (),
                      "I'm not getting this right. Let me put you through to a human.",
                      terminal=True)


def readback(summary: str) -> RepairMove:
    """Single commit-time confirmation for consequential fields. Not a repair."""
    return RepairMove(MoveKind.READBACK, None, (), f"{summary} — correct?")
