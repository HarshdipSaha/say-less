from evalharness.simulator import respond
from sayless.moves import (escalate, open_request, restricted_offer,
                           restricted_request, two_way_offer)


def test_correct_offer_is_confirmed_with_one_word_of_real_audio():
    r = respond(restricted_offer("day", "Tuesday"), truth="Tuesday", answer_words=1)
    assert r.accepted and r.words == 1 and r.audio == "yes" and r.value == "Tuesday"


def test_wrong_offer_is_rejected_and_costs_one_word():
    r = respond(restricted_offer("day", "Thursday"), truth="Tuesday", answer_words=1)
    assert not r.accepted and r.words == 1 and r.audio == "no"


def test_two_way_offer_returns_the_candidate_that_matched():
    r = respond(two_way_offer("day", "Tuesday", "Thursday"), truth="Thursday", answer_words=1)
    assert r.accepted and r.value == "Thursday" and r.audio == "answer"


def test_two_way_offer_missing_the_truth_is_rejected():
    r = respond(two_way_offer("day", "Monday", "Friday"), truth="Tuesday", answer_words=1)
    assert not r.accepted and r.audio == "no"


def test_category_question_replays_the_answer_clip_and_charges_its_words():
    r = respond(restricted_request("day", "day"), truth="beard trim", answer_words=2)
    assert r.audio == "answer" and r.words == 2


def test_open_request_replays_take_two_and_charges_the_sentence():
    r = respond(open_request(), truth="Tuesday", answer_words=1, sentence_words=7)
    assert r.audio == "take2" and r.words == 7 and not r.accepted


def test_escalation_ends_the_call():
    r = respond(escalate(), truth="Tuesday", answer_words=1)
    assert r.audio == "none" and r.terminal
