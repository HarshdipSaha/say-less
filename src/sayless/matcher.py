"""Phonetic ranking of a heard value against a field's allowed values.

The recogniser gives no alternative hypotheses, so every candidate offered in a
repair originates here.

Thresholds are empirical, measured before they were written down:
    phonetic_score("chewsday", "Tuesday")      = 0.6667   -> must be STRONG
    phonetic_score("refrigerator", best day)   = 0.5533   -> must not be STRONG
"""
from dataclasses import dataclass

from metaphone import doublemetaphone
from rapidfuzz import fuzz

STRONG = 0.65        # worth naming out loud
CLEAR_LEAD = 0.06    # gap that makes one candidate dominate the next


def phonetic_score(heard: str, candidate: str) -> float:
    """0..1 similarity, weighted toward sound rather than spelling."""
    hc = [c for c in doublemetaphone(heard) if c]
    cc = [c for c in doublemetaphone(candidate) if c]
    code = max((fuzz.ratio(a, b) for a in hc for b in cc), default=0) / 100
    literal = fuzz.ratio(heard.lower(), candidate.lower()) / 100
    return round(0.7 * code + 0.3 * literal, 4)


@dataclass(frozen=True)
class MatchResult:
    heard: str
    in_set: bool
    candidates: tuple[tuple[str, float], ...]     # sorted, highest score first

    def strong(self, threshold: float = STRONG) -> tuple[tuple[str, float], ...]:
        """Candidates worth naming out loud. The threshold is per-field because
        a large value set produces a plausible-looking match for almost anything."""
        return tuple(c for c in self.candidates if c[1] >= threshold)


def match(heard: str, values: tuple[str, ...]) -> MatchResult:
    cleaned = heard.strip().strip(".,?!").lower()
    ranked = sorted(((v, phonetic_score(cleaned, v)) for v in values),
                    key=lambda p: p[1], reverse=True)
    return MatchResult(cleaned, cleaned in {v.lower() for v in values}, tuple(ranked))
