from sayless.moves import (MoveKind, escalate, open_request, readback,
                           restricted_offer, restricted_request, two_way_offer)


def test_restricted_offer_names_the_candidate():
    m = restricted_offer("day", "Tuesday")
    assert m.kind is MoveKind.RESTRICTED_OFFER
    assert m.candidates == ("Tuesday",) and "Tuesday" in m.utterance


def test_two_way_offer_names_both():
    m = two_way_offer("day", "Tuesday", "Thursday")
    assert m.candidates == ("Tuesday", "Thursday")
    assert " or " in m.utterance


def test_restricted_request_names_the_field_not_a_value():
    m = restricted_request("day", "day")
    assert m.candidates == () and "day" in m.utterance.lower()


def test_open_request_names_nothing():
    m = open_request()
    assert m.field is None and m.candidates == ()


def test_escalate_is_terminal_and_visible():
    m = escalate()
    assert m.kind is MoveKind.ESCALATE and m.terminal is True
    assert "human" in m.utterance.lower()


def test_readback_is_not_a_repair_move():
    assert readback("x on Tuesday").kind is MoveKind.READBACK


def test_moves_are_ordered_by_specificity():
    ordered = [MoveKind.OPEN_REQUEST, MoveKind.RESTRICTED_REQUEST,
               MoveKind.TWO_WAY_OFFER, MoveKind.RESTRICTED_OFFER]
    assert [m.specificity for m in ordered] == sorted(m.specificity for m in ordered)
