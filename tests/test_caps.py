from sayless.moves import MoveKind
from sayless.planner import (MAX_REPAIRS_PER_SESSION, RepairState, plan_repair)
from sayless.schema import BOOKING_SCHEMA
from tests.helpers import bound, turn

T = turn([("chewsday", 0.4)])
F = [bound("day", "chewsday", 0)]


def test_second_trouble_on_the_same_field_degrades_to_open_request():
    state = RepairState()
    first = plan_repair(T, F, BOOKING_SCHEMA, state)
    assert first.kind is MoveKind.RESTRICTED_OFFER
    state.record(first)
    state.new_turn()
    assert plan_repair(T, F, BOOKING_SCHEMA, state).kind is MoveKind.OPEN_REQUEST


def test_two_repairs_within_one_turn_escalate():
    state = RepairState()
    state.record(plan_repair(T, F, BOOKING_SCHEMA, state))
    state.record(plan_repair(T, F, BOOKING_SCHEMA, state))
    assert plan_repair(T, F, BOOKING_SCHEMA, state).kind is MoveKind.ESCALATE


def test_session_budget_escalates():
    state = RepairState()
    for _ in range(MAX_REPAIRS_PER_SESSION):
        move = plan_repair(T, F, BOOKING_SCHEMA, state)
        state.record(move)
        state.new_turn()
    assert plan_repair(T, F, BOOKING_SCHEMA, state).kind is MoveKind.ESCALATE


def test_new_turn_resets_the_turn_counter_but_not_the_field_cap():
    state = RepairState()
    state.record(plan_repair(T, F, BOOKING_SCHEMA, state))
    state.new_turn()
    assert state.repairs_this_turn == 0
    assert state.offers["day"] == 1


def test_after_escalation_the_planner_is_silent():
    state = RepairState()
    state.record(plan_repair(T, F, BOOKING_SCHEMA, state))
    state.escalated = True
    assert plan_repair(T, F, BOOKING_SCHEMA, state) is None


def test_a_clean_turn_after_a_spent_budget_is_accepted_not_escalated():
    """A caller who has finally been understood must not be handed to a human
    because earlier turns were hard. Both budgets are checked only where trouble
    was found."""
    from sayless.baseline import plan_repair_baseline
    state = RepairState()
    state.repairs_total = MAX_REPAIRS_PER_SESSION
    clean_turn = turn([("Tuesday", 0.99)])
    clean_field = [bound("day", "Tuesday", 0)]
    assert plan_repair(clean_turn, clean_field, BOOKING_SCHEMA, state) is None
    assert plan_repair_baseline(clean_turn, clean_field, BOOKING_SCHEMA, state) is None
