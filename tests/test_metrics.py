from evalharness.metrics import RunRecord, aggregate


def test_words_re_said_counts_only_repair_induced_turns():
    r = RunRecord("day_01", "day", "Tuesday", "Tuesday", 2, 1, False, False, False)
    agg = aggregate([r])
    assert agg["words_re_said"] == 1.0
    assert agg["turns_to_resolution"] == 2.0
    assert agg["commit_accuracy"] == 1.0
    assert agg["escalation_rate"] == 0.0


def test_commit_accuracy_counts_exact_matches_only():
    rs = [RunRecord("a", "day", "Tuesday", "Tuesday", 1, 0, False, False, False),
          RunRecord("b", "day", "Tuesday", "Thursday", 1, 0, True, True, False)]
    assert aggregate(rs)["commit_accuracy"] == 0.5


def test_residual_is_the_share_of_errors_that_were_in_set_and_confident():
    rs = [RunRecord("a", "day", "Tuesday", "Thursday", 1, 0, True, True, False),
          RunRecord("b", "day", "Tuesday", "chewsday", 1, 0, False, False, False)]
    assert aggregate(rs)["residual"] == 0.5


def test_escalation_is_reported():
    rs = [RunRecord("a", "day", "Tuesday", None, 4, 9, False, False, True)]
    assert aggregate(rs)["escalation_rate"] == 1.0
