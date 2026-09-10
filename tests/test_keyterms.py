from sayless.keyterms import prospective_terms, reactive_terms
from sayless.moves import open_request, restricted_offer, two_way_offer
from sayless.schema import BOOKING_SCHEMA


def test_prospective_terms_are_the_expected_fields_value_sets():
    terms = prospective_terms(["day"], BOOKING_SCHEMA)
    assert "Tuesday" in terms and len(terms) == 7


def test_prospective_terms_respect_the_api_cap_with_real_data():
    terms = prospective_terms(list(BOOKING_SCHEMA), BOOKING_SCHEMA)
    assert len(terms) == 100 and all(len(t) <= 50 for t in terms)


def test_reactive_terms_narrow_to_the_candidates_in_play():
    assert reactive_terms(two_way_offer("day", "Tuesday", "Thursday")) == ["Tuesday", "Thursday"]
    assert reactive_terms(restricted_offer("day", "Tuesday")) == ["Tuesday", "yes", "no"]
    assert reactive_terms(open_request()) == []


def test_reactive_terms_can_be_disabled_for_measurement():
    assert reactive_terms(restricted_offer("day", "Tuesday"), enabled=False) == []
