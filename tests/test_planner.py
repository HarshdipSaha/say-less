import pytest
from sayless.moves import MoveKind
from sayless.planner import RepairState, plan_repair
from sayless.schema import BOOKING_SCHEMA, FieldSpec
from tests.helpers import bound, turn

CASES = [
    ("in set and confident -> silence",
     [("book", 0.99), ("Tuesday", 0.95)], 0.9, [bound("day", "Tuesday", 1)], None, None),

    # Production is confidence-independent (docs/STATUS.md gate result:
    # confidence did not separate correct from misheard tokens, so
    # CONFIDENCE_THRESHOLD = 0.0). An in-set value is therefore accepted
    # regardless of how low its confidence reads -- the "shaky" branch below
    # is what would fire if a nonzero threshold were configured; see
    # test_shaky_in_set_value_triggers_a_repair_when_a_threshold_is_set for
    # proof the mechanism itself still works.
    ("in set, low confidence, confidence-independent config -> silence anyway",
     [("book", 0.99), ("Tuesday", 0.02)], 0.9, [bound("day", "Tuesday", 1)], None, None),

    ("out of set, one strong candidate -> offer it",
     [("book", 0.99), ("chewsday", 0.40)], 0.9, [bound("day", "chewsday", 1)],
     MoveKind.RESTRICTED_OFFER, ("Tuesday",)),

    ("out of set, nothing plausible -> ask the category",
     [("book", 0.99), ("refrigerator", 0.50)], 0.9, [bound("day", "refrigerator", 1)],
     MoveKind.RESTRICTED_REQUEST, ()),

    ("no field bound -> open request",
     [("mumble", 0.20)], 0.9, [], MoveKind.OPEN_REQUEST, ()),

    ("turn-level trouble -> open request even with a bound field",
     [("book", 0.99), ("Tuesday", 0.95)], 0.10, [bound("day", "Tuesday", 1)],
     MoveKind.OPEN_REQUEST, ()),
]


@pytest.mark.parametrize("name,words,eot,fields,kind,cands",
                         CASES, ids=[c[0] for c in CASES])
def test_ladder(name, words, eot, fields, kind, cands):
    move = plan_repair(turn(words, eot), fields, BOOKING_SCHEMA, RepairState())
    if kind is None:
        assert move is None
        return
    assert move.kind is kind
    if cands:
        assert move.candidates == cands


def test_shaky_in_set_value_triggers_a_repair_when_a_threshold_is_set():
    """The confidence-secondary-signal mechanism is real code, not dead code --
    it is simply configured off in production because the gate found confidence
    didn't discriminate. Prove it still fires given a schema that sets a
    nonzero confidence_threshold, independent of the production BOOKING_SCHEMA."""
    thresholded_schema = {"day": FieldSpec("day", "day", BOOKING_SCHEMA["day"].values,
                                           confidence_threshold=0.65)}
    move = plan_repair(turn([("book", 0.99), ("Tuesday", 0.30)]),
                       [bound("day", "Tuesday", 1)], thresholded_schema, RepairState())
    assert move.kind is MoveKind.RESTRICTED_OFFER and move.candidates == ("Tuesday",)


def test_choose_asks_the_category_when_three_candidates_tie():
    """Tests _choose directly with a constructed tie, because building an
    utterance that produces a real three-way tie is brittle. An assertion that
    accepts every possible return value verifies nothing."""
    from sayless.planner import _choose
    from sayless.schema import BOOKING_SCHEMA as S
    tie = (("Rao", 0.90), ("Roy", 0.89), ("Ray", 0.885))
    assert _choose("surname", S["surname"], tie).kind is MoveKind.RESTRICTED_REQUEST


def test_choose_offers_one_when_it_clearly_leads():
    from sayless.planner import _choose
    from sayless.schema import BOOKING_SCHEMA as S
    lead = (("Sharma", 0.93), ("Varma", 0.80))
    move = _choose("surname", S["surname"], lead)
    assert move.kind is MoveKind.RESTRICTED_OFFER and move.candidates == ("Sharma",)


def test_a_realistic_surname_confusion_still_clears_the_raised_bar():
    """The surname bar is 0.80 rather than the global 0.65 because a large value
    set matches almost anything. Verify the bar did not exclude the real case."""
    from sayless.matcher import match
    from sayless.schema import BOOKING_SCHEMA as S
    spec = S["surname"]
    strong = match("shurma", spec.values).strong(spec.strong_threshold)
    assert strong and strong[0][0] == "Sharma"


def test_nonsense_against_the_surname_set_is_not_offered_a_name():
    from sayless.matcher import match
    from sayless.schema import BOOKING_SCHEMA as S
    spec = S["surname"]
    assert match("zzzzq", spec.values).strong(spec.strong_threshold) == ()


def test_first_troubled_field_wins_when_several_are_bad():
    fields = [bound("day", "chewsday", 0), bound("service", "haircut", 1)]
    move = plan_repair(turn([("chewsday", 0.4), ("haircut", 0.99)]),
                       fields, BOOKING_SCHEMA, RepairState())
    assert move.field == "day"
