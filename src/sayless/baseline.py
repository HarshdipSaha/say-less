"""Baseline planner: current deployed voice-agent behaviour.

Asks a generic re-ask when a bound value is below threshold or nothing bound.
Has no notion of a value set, so it cannot see a confidently wrong value.

Shares every cap and every threshold with the Say Less planner. The two arms
differ in one place only: which move is returned.
"""
from .evidence import BoundField, TurnEvidence
from .moves import RepairMove, escalate, open_request
from .planner import (MAX_REPAIRS_PER_SESSION, MAX_REPAIRS_PER_TURN,
                      TURN_TROUBLE_THRESHOLD, RepairState)
from .schema import FieldSpec


def plan_repair_baseline(turn: TurnEvidence,
                         bound_fields: list[BoundField],
                         schema: dict[str, FieldSpec],
                         state: RepairState) -> RepairMove | None:
    if state.escalated:
        return None

    # Both budget checks sit inside the trouble branches, exactly as they do in
    # plan_repair. Checking them up front would make this arm escalate on a
    # clean confident turn where the seam stays silent, which is an asymmetry in
    # the one module whose whole purpose is to differ in exactly one place.
    def _budget_spent() -> bool:
        return (state.repairs_total >= MAX_REPAIRS_PER_SESSION
                or state.repairs_this_turn >= MAX_REPAIRS_PER_TURN)

    if not bound_fields or turn.end_of_turn_confidence < TURN_TROUBLE_THRESHOLD:
        return escalate() if _budget_spent() else open_request()

    for bf in bound_fields:
        spec = schema.get(bf.field)
        if spec is None:
            continue
        if turn.min_confidence(bf.word_indices) < spec.confidence_threshold:
            return escalate() if _budget_spent() else open_request()
    return None
