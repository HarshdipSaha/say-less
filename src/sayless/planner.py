"""The repair planner. Pure function from evidence to a repair move.

The trigger is set membership first and confidence second. A confidently wrong
word is invisible to confidence by construction, so confidence is never the
primary signal.
"""
from dataclasses import dataclass, field as dc_field

from .evidence import BoundField, TurnEvidence
from .matcher import CLEAR_LEAD, match
from .moves import (MoveKind, RepairMove, escalate, open_request,
                    restricted_offer, restricted_request, two_way_offer)
from .schema import FieldSpec

TURN_TROUBLE_THRESHOLD = 0.30
MAX_OFFERS_PER_FIELD = 1
MAX_REPAIRS_PER_TURN = 2
MAX_REPAIRS_PER_SESSION = 4


@dataclass
class RepairState:
    """Caps. A clarification loop is worse than any single mishearing."""
    offers: dict[str, int] = dc_field(default_factory=dict)
    repairs_this_turn: int = 0
    repairs_total: int = 0
    escalated: bool = False

    def record(self, move: RepairMove) -> None:
        if move.kind is MoveKind.READBACK:
            return                      # never let a readback clear escalation
        if move.kind is MoveKind.ESCALATE:
            self.escalated = True
            return
        self.repairs_this_turn += 1
        self.repairs_total += 1
        if move.field and move.kind in (MoveKind.RESTRICTED_OFFER, MoveKind.TWO_WAY_OFFER):
            self.offers[move.field] = self.offers.get(move.field, 0) + 1

    def new_turn(self) -> None:
        self.repairs_this_turn = 0


def _choose(field: str, spec: FieldSpec, strong) -> RepairMove:
    """Pick the most specific move the candidate distribution supports."""
    if not strong:
        return restricted_request(field, spec.label)
    if len(strong) == 1:
        return restricted_offer(field, strong[0][0])
    if strong[0][1] - strong[1][1] > CLEAR_LEAD:
        return restricted_offer(field, strong[0][0])            # one dominates
    if len(strong) == 2 or (strong[1][1] - strong[2][1]) > CLEAR_LEAD:
        return two_way_offer(field, strong[0][0], strong[1][0])  # two dominate
    return restricted_request(field, spec.label)                # too many, ask category


def plan_after_rejection(field: str, spec: FieldSpec,
                         state: RepairState) -> RepairMove:
    """Follow-up when the caller rejects an offer, under the same caps.

    A rejection does not buy a second guess. The field's offer budget is one,
    and the offer that was just rejected spent it, so this degrades to the
    category question and then to escalation. That is the spec's ladder, and it
    is what a competent human agent does: told "no" after "Sharma?", they ask
    you to spell it rather than guessing a second name.

    An earlier revision ranked a replacement candidate here. It was unreachable
    -- the offer is always recorded before the caller can reject it, so the
    budget check always fired first -- and it existed only because the rejection
    branch used to live outside the planner and had no caps at all.
    """
    if state.escalated or state.repairs_total >= MAX_REPAIRS_PER_SESSION:
        return escalate()
    return restricted_request(field, spec.label)


def plan_repair(turn: TurnEvidence,
                bound_fields: list[BoundField],
                schema: dict[str, FieldSpec],
                state: RepairState) -> RepairMove | None:
    """Return the most specific repair the evidence supports, or None to accept."""
    if state.escalated:
        return None

    # Both budgets are checked only where trouble was actually found. Checking
    # them up front would hand the call to a human on a clean, confident,
    # in-set turn just because earlier turns were hard -- a live-demo killer,
    # and the opposite of what a caller who has finally been understood wants.
    def _budget_spent() -> bool:
        return (state.repairs_total >= MAX_REPAIRS_PER_SESSION
                or state.repairs_this_turn >= MAX_REPAIRS_PER_TURN)

    if not bound_fields or turn.end_of_turn_confidence < TURN_TROUBLE_THRESHOLD:
        return escalate() if _budget_spent() else open_request()

    for bf in bound_fields:
        spec = schema.get(bf.field)
        if spec is None:
            continue

        result = match(bf.heard_value, spec.values)
        confidence = turn.min_confidence(bf.word_indices)

        if result.in_set and confidence >= spec.confidence_threshold:
            continue                                   # accept silently

        if _budget_spent():
            return escalate()
        if state.offers.get(bf.field, 0) >= MAX_OFFERS_PER_FIELD:
            return open_request()                      # this field had its one offer

        return _choose(bf.field, spec, result.strong(spec.strong_threshold))

    return None
