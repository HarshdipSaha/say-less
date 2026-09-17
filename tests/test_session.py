import pytest

from sayless.evidence import BoundField
from sayless.moves import MoveKind, restricted_offer
from sayless.planner import MAX_REPAIRS_PER_SESSION, RepairState, plan_after_rejection
from sayless.schema import BOOKING_SCHEMA
from sayless.session import BookingSession, named_value
from tests.helpers import turn


def offered(session, field, candidate):
    """Put an offer on the table exactly as handle_turn would have."""
    move = restricted_offer(field, candidate)
    session.state.record(move)
    session.pending = move
    return session


def test_named_value_accepts_a_bare_value_after_a_negation():
    assert named_value("no friday", BOOKING_SCHEMA["day"]) == "Friday"
    assert named_value("no, it's Friday.", BOOKING_SCHEMA["day"]) == "Friday"


def test_named_value_accepts_a_multi_word_service():
    assert named_value("i said beard trim", BOOKING_SCHEMA["service"]) == "beard trim"


def test_named_value_returns_nothing_for_a_bare_yes_or_no():
    assert named_value("no", BOOKING_SCHEMA["day"]) is None
    assert named_value("yes", BOOKING_SCHEMA["day"]) is None


@pytest.mark.parametrize("said", [
    "no thats the wrong day",
    "no i think you got the day wrong",
    "not the right day at all",
    "no i said the day",          # reduces to "day", a field name, not a surname
    "no the price is wrong",
    "no that was long",           # reduces to "long"
    "no it was green",
    "not cook",
    "no it was a bell",
    "no that is wood",
    "no the west",
    "no, young",
])
def test_a_complaint_mentioning_a_surname_word_is_not_taken_as_a_surname(said):
    """Public surname frequency lists contain Day, Green, King, Price, Cook,
    Bell, Wood, West, Long and Young. Without the stop-list these all reduce to
    a bare word that is a valid surname, and the agent writes it into the one
    field marked consequential.

    These cases pass trivially against the 20-name starter list and fail the
    moment Task 3 Step 1 is followed and the list is extended from a public
    source -- the same silent-until-later shape as an off-by-one in fixture data.
    Run this suite again after extending `corpus/surnames.txt`."""
    from sayless.session import RESERVED
    assert named_value(said, BOOKING_SCHEMA["surname"], RESERVED) is None


def test_a_caller_genuinely_naming_their_surname_is_still_accepted():
    """The guard must not swallow real corrections."""
    from sayless.session import RESERVED
    spec = BOOKING_SCHEMA["surname"]
    target = next(v for v in spec.values if v.lower() not in RESERVED)
    assert named_value(f"no my name is {target}", spec, RESERVED) == target


def test_a_stop_listed_surname_still_binds_on_the_next_turn():
    """The stop-list gates only the same-turn shortcut. A caller named Long is
    not locked out; they get a category question and bind through the binder."""
    from sayless.session import RESERVED
    spec = BOOKING_SCHEMA["surname"]
    stopped = next((v for v in spec.values if v.lower() in RESERVED), None)
    if stopped is None:
        pytest.skip("starter surname list contains no stop-listed name")
    assert named_value(f"no {stopped}", spec, RESERVED) is None
    s = offered(BookingSession(), "surname", "Sharma")
    s._answer_to_pending(f"no {stopped}")
    assert s.pending.kind is MoveKind.RESTRICTED_REQUEST   # not a dead end


def test_nothing_is_committed_from_a_turn_the_planner_treats_as_suspect():
    """Locks the boundary that currently agrees with TURN_TROUBLE_THRESHOLD
    only by convention."""
    from sayless.evidence import BoundField
    s = BookingSession()
    s._commit_clean([BoundField("service", "haircut", (0,))],
                    turn([("haircut", 0.97)], eot=0.10))
    assert s.values == {}


def test_clean_fields_survive_a_repair_on_a_different_field():
    """Say "a haircut on chewsday" and the service must not have to be repeated.
    Re-asking a word the agent already heard is the cost this project reduces."""
    from sayless.evidence import BoundField
    s = BookingSession()
    t = turn([("haircut", 0.97), ("chewsday", 0.40)], eot=0.9)
    s._commit_clean([BoundField("service", "haircut", (0,)),
                     BoundField("day", "chewsday", (1,))], t)
    assert s.values == {"service": "haircut"}, "day is under repair, service is not"


def test_rejection_that_names_a_value_accepts_it():
    s = offered(BookingSession(), "day", "Tuesday")
    s._answer_to_pending("no friday")
    assert s.values["day"] == "Friday" and s.pending is None


def test_a_rejection_does_not_buy_a_second_named_guess():
    s = offered(BookingSession(), "day", "Tuesday")
    s._answer_to_pending("no")
    assert s.pending.kind is MoveKind.RESTRICTED_REQUEST
    assert s.pending.candidates == ()


def test_repeated_rejection_terminates_in_escalation():
    """Ten consecutive rejections must end the call, not enumerate the value set."""
    s = offered(BookingSession(), "surname", "Sharma")
    named = 0
    for _ in range(10):
        if s.done or s.pending is None:
            break
        s._answer_to_pending("no")
        if s.pending and s.pending.candidates:
            named += 1
    assert named == 0, "no further named guesses after the field budget is spent"
    assert s.done and s.state.escalated


def test_plan_after_rejection_escalates_once_the_session_budget_is_spent():
    state = RepairState()
    state.repairs_total = MAX_REPAIRS_PER_SESSION
    assert plan_after_rejection("day", BOOKING_SCHEMA["day"], state).kind is MoveKind.ESCALATE


def test_plan_after_rejection_never_names_a_candidate():
    """One offer per field is the whole rule. Assert on the value, not on the
    absence of one particular string, which any implementation would satisfy."""
    move = plan_after_rejection("day", BOOKING_SCHEMA["day"], RepairState())
    assert move.kind is MoveKind.RESTRICTED_REQUEST
    assert move.candidates == ()
    assert "day" in move.utterance.lower()


def test_a_bare_answer_to_the_field_just_asked_is_taken_without_the_binder(monkeypatch):
    """"And the last name?" -> "It's Bennett." must bind. The LLM binder was
    observed returning nothing for a one-word reply with no sentence context
    (live, 2026-09-17), so the session takes a reply that reduces to a value
    from the asked field's set directly, the same way _answer_to_pending does."""
    import sayless.session as sess
    monkeypatch.setattr(sess, "bind", lambda *a, **k: pytest.fail("binder must not be called"))
    s = BookingSession()
    s.values.update({"service": "haircut", "day": "Tuesday", "time": "two pm"})
    s.asked = "surname"
    reply, _ = s.handle_turn(turn([("It's", 1.0), ("Bennett.", 0.97)], transcript="It's Bennett."))
    assert s.values["surname"] == "Bennett"
    assert reply.endswith("correct?")           # moved straight on to the readback


def test_a_bare_answer_to_a_category_question_is_taken_directly(monkeypatch):
    """"Which service?" (a restricted request, no candidate on the table) ->
    "a haircut please" resolves without a second binder round trip."""
    import sayless.session as sess
    from sayless.moves import restricted_request
    monkeypatch.setattr(sess, "bind", lambda *a, **k: pytest.fail("binder must not be called"))
    s = BookingSession()
    s.pending = restricted_request("service", "service")
    reply, _ = s.handle_turn(turn([("a", 1.0), ("haircut", 0.93), ("please", 1.0)],
                                  transcript="a haircut please"))
    assert s.values["service"] == "haircut" and s.pending is None
    assert reply == "And the day?"


def test_a_suspect_turn_does_not_take_the_bare_answer_shortcut(monkeypatch):
    """The shortcut shares _commit_clean's turn-level guard: a turn the planner
    would treat as trouble goes through the full bind/plan path instead."""
    import sayless.session as sess
    calls = []
    monkeypatch.setattr(sess, "bind", lambda *a, **k: calls.append(1) or [])
    s = BookingSession()
    s.asked = "day"
    s.handle_turn(turn([("Friday", 0.9)], eot=0.10, transcript="Friday"))
    assert calls and "day" not in s.values


def test_the_asked_field_is_recorded_by_advance():
    s = BookingSession()
    s.values.update({"service": "haircut"})
    reply, _ = s._advance()
    assert reply == "And the day?" and s.asked == "day"
    s.values.update({"day": "Tuesday", "time": "two pm", "surname": "Bennett"})
    s._advance()
    assert s.asked is None and s.awaiting_readback
