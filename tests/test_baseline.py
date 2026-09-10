from sayless.baseline import plan_repair_baseline
from sayless.moves import MoveKind
from sayless.planner import RepairState
from sayless.schema import BOOKING_SCHEMA
from tests.helpers import bound, turn


def test_baseline_never_names_a_candidate():
    move = plan_repair_baseline(turn([("chewsday", 0.4)]),
                                [bound("day", "chewsday", 0)],
                                BOOKING_SCHEMA, RepairState())
    assert move.kind is MoveKind.OPEN_REQUEST and move.candidates == ()


def test_baseline_accepts_when_confident():
    assert plan_repair_baseline(turn([("Tuesday", 0.95)]),
                                [bound("day", "Tuesday", 0)],
                                BOOKING_SCHEMA, RepairState()) is None


def test_baseline_cannot_see_a_confidently_wrong_value():
    """The failure Say Less exists to catch."""
    assert plan_repair_baseline(turn([("Thursday", 0.95)]),
                                [bound("day", "Thursday", 0)],
                                BOOKING_SCHEMA, RepairState()) is None


def test_baseline_uses_the_same_threshold_as_the_schema():
    from sayless.schema import BOOKING_SCHEMA as S
    spec = S["day"]
    just_below = spec.confidence_threshold - 0.01
    if just_below < 0:
        return                      # confidence-independent mode; nothing to assert
    assert plan_repair_baseline(turn([("Tuesday", just_below)]),
                                [bound("day", "Tuesday", 0)],
                                S, RepairState()) is not None


def test_baseline_escalates_on_the_session_budget():
    state = RepairState()
    t, f = turn([("x", 0.1)]), [bound("day", "x", 0)]
    for _ in range(4):
        state.record(plan_repair_baseline(t, f, BOOKING_SCHEMA, state))
        state.new_turn()
    assert plan_repair_baseline(t, f, BOOKING_SCHEMA, state).kind is MoveKind.ESCALATE
