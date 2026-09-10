"""Substitute the <!-- METRICS_TABLE --> placeholder in README.md with the
real table from eval_results.json, plus a business-value note computed from
whichever measured delta is actually load-bearing in this run.

Not part of the plan's numbered tasks -- a small convenience script so the
README's numbers are read out of the actual results file rather than typed
by hand and risking a transcription error.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Human-agent recovery cost for a booking that went out wrong, cited range
# from industry figures gathered during this project's research phase
# (traditional US contact-centre agent cost per inbound call, loaded):
# roughly $7-12/call. Used here only if commit accuracy actually differs
# between arms -- if a run shows no accuracy delta, no figure is invented.
RECOVERY_COST_LOW, RECOVERY_COST_HIGH = 7, 12
CALLS = 10_000

# Only used as a secondary note if turns actually moved in this run.
COST_PER_MINUTE = 0.16
SECONDS_PER_TURN = 15


def main() -> None:
    results = json.loads((ROOT / "eval_results.json").read_text())
    b, s = results["baseline"], results["sayless"]

    table = (
        "| Metric | Baseline | Say Less |\n"
        "|---|---|---|\n"
        f"| Words re-said per booking | {b['words_re_said']:.2f} | {s['words_re_said']:.2f} |\n"
        f"| Turns to resolution | {b['turns_to_resolution']:.2f} | {s['turns_to_resolution']:.2f} |\n"
        f"| Commit accuracy | {b['commit_accuracy']:.0%} | {s['commit_accuracy']:.0%} |\n"
        f"| Escalated to a human | {b['escalation_rate']:.0%} | {s['escalation_rate']:.0%} |\n"
        f"| Residual (not solvable) | {b['residual']:.0%} | {s['residual']:.0%} |\n"
    )

    acc_delta = s["commit_accuracy"] - b["commit_accuracy"]
    turn_delta = b["turns_to_resolution"] - s["turns_to_resolution"]

    parts = ["\n**Business value, from the measured numbers.**"]

    if acc_delta > 0:
        wrong_avoided = acc_delta * CALLS
        low, high = wrong_avoided * RECOVERY_COST_LOW, wrong_avoided * RECOVERY_COST_HIGH
        parts.append(
            f" Commit accuracy: {b['commit_accuracy']:.0%} (baseline) vs "
            f"{s['commit_accuracy']:.0%} (Say Less) on this corpus. The baseline case that "
            "differs committed a value one character off from every member of its own allowed "
            "list (a near-miss the recogniser produced with high confidence) -- Say Less caught "
            "it because the value wasn't an exact member of the set, not because confidence "
            "flagged it. At this accuracy delta, roughly "
            f"**{wrong_avoided:,.0f} wrong bookings per {CALLS:,} calls** go out silently "
            "wrong under the baseline and get caught under Say Less. Using a typical loaded "
            "human-agent recovery-call cost of "
            f"${RECOVERY_COST_LOW}-{RECOVERY_COST_HIGH} "
            "([Retell AI, \"Call Center Outsourcing Costs in 2026\"]"
            "(https://www.retellai.com/blog/call-center-outsourcing-costs)), "
            f"that is **${low:,.0f}-${high:,.0f} per {CALLS:,} calls** in avoided recovery cost "
            "alone, before counting the cost of a customer who received a wrong booking and "
            "never called back to report it."
        )
    else:
        parts.append(" Commit accuracy was equal in this run; no accuracy-based figure is claimed.")

    if abs(turn_delta) > 0.005:
        seconds = turn_delta * SECONDS_PER_TURN
        dollars_per_call = (seconds / 60) * COST_PER_MINUTE
        parts.append(
            f" Turns to resolution moved by {turn_delta:+.2f} per booking; at "
            f"~{SECONDS_PER_TURN}s/turn and ${COST_PER_MINUTE:.2f}/minute "
            "([Aircall, \"AI Voice Agent Pricing in 2026\"](https://aircall.io/blog/best-practices/ai-voice-agent-cost/)), "
            f"that is ${dollars_per_call * CALLS:+,.0f} per {CALLS:,} calls."
        )
    else:
        parts.append(
            f" Turns to resolution was effectively unchanged ({b['turns_to_resolution']:.2f} vs "
            f"{s['turns_to_resolution']:.2f}) on this corpus: the one case Say Less repaired was "
            "resolved with a single one-word confirmation, not a full extra turn, because the "
            "offer was accepted on the first try."
        )

    value_note = "".join(parts) + "\n"

    readme = ROOT / "README.md"
    text = readme.read_text()
    text = text.replace("<!-- METRICS_TABLE -->", table + value_note)
    text = text.replace(
        "_Numbers below are placeholders pending a harness run with the "
        "corrected binder prompt (see \"Known issues found and fixed during "
        "the build\" below) — updated once `python -m evalharness.run` "
        "completes cleanly._\n\n",
        "",
    )
    readme.write_text(text)
    print("README.md updated.")
    print(table)
    print(value_note)


if __name__ == "__main__":
    main()
