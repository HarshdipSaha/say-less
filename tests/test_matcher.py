from sayless.matcher import STRONG, match, phonetic_score
from sayless.schema import DAYS, load_surnames


def test_exact_member_is_in_set_and_ranks_first():
    r = match("Tuesday", DAYS)
    assert r.in_set is True and r.candidates[0][0] == "Tuesday"


def test_matching_is_case_insensitive():
    assert match("tuesday", DAYS).in_set is True


def test_the_measured_confusion_clears_the_strong_threshold():
    """Verified: phonetic_score('chewsday','Tuesday') == 0.6667."""
    assert phonetic_score("chewsday", "Tuesday") >= STRONG
    r = match("chewsday", DAYS)
    assert r.in_set is False and r.strong()[0][0] == "Tuesday"


def test_unrelated_input_produces_no_strong_candidate():
    """Verified: best score for 'refrigerator' against DAYS is 0.5533."""
    assert match("refrigerator", DAYS).strong() == ()


def test_surname_confusion_is_recoverable():
    assert match("hardip", load_surnames()).candidates[0][0] == "Hardeep"


def test_multi_word_value_matches():
    services = ("beard trim", "haircut")
    assert match("beard trum", services).candidates[0][0] == "beard trim"


def test_score_is_bounded():
    assert 0.0 <= phonetic_score("a", "zzzz") <= 1.0
    assert phonetic_score("Tuesday", "Tuesday") > 0.95
