"""The numbers that are the deliverable."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RunRecord:
    item_id: str
    field: str
    truth: str
    committed: str | None
    turns: int                  # turns from first mention to a committed value
    repair_words: int           # words the caller uttered only because of a repair
    wrong_was_in_set: bool
    wrong_was_confident: bool
    escalated: bool


def aggregate(records: list[RunRecord]) -> dict[str, float]:
    n = len(records)
    if n == 0:
        return {"n": 0}
    correct = sum(1 for r in records if r.committed == r.truth)
    errors = [r for r in records if r.committed != r.truth]
    residual = sum(1 for r in errors if r.wrong_was_in_set and r.wrong_was_confident)
    return {
        "n": float(n),
        "words_re_said": sum(r.repair_words for r in records) / n,
        "turns_to_resolution": sum(r.turns for r in records) / n,
        "commit_accuracy": correct / n,
        "escalation_rate": sum(1 for r in records if r.escalated) / n,
        "residual": (residual / len(errors)) if errors else 0.0,
    }


def table(baseline: dict, sayless: dict) -> str:
    rows = [("Words re-said per booking", "words_re_said", "{:.2f}"),
            ("Turns to resolution", "turns_to_resolution", "{:.2f}"),
            ("Commit accuracy", "commit_accuracy", "{:.0%}"),
            ("Escalated to a human", "escalation_rate", "{:.0%}"),
            ("Residual (not solvable)", "residual", "{:.0%}")]
    out = ["| Metric | Baseline | Say Less |", "|---|---|---|"]
    for label, key, fmt in rows:
        out.append(f"| {label} | {fmt.format(baseline[key])} | {fmt.format(sayless[key])} |")
    return "\n".join(out)
