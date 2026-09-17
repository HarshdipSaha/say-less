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

# AssemblyAI's inverse-text-normalisation renders a spoken hour as a digit
# ("one pm" -> "1 pm"), but schema.py's TIMES values are spelled out. A bare
# digit has nothing for doublemetaphone to encode, so without this the
# phonetic ranking falls back almost entirely to literal string similarity and
# silently prefers an unrelated spelled-out value: verified, "1 pm" against
# TIMES ranked "two pm" (0.74) above the correct "one pm" (0.6467), well past
# STRONG and CLEAR_LEAD, meaning Say Less would have confidently offered the
# wrong hour out loud. Found while sourcing real SLURP time-of-day clips for
# the benchmark expansion (2026-09-17) -- every clean recording of a spoken
# hour came back from the real API as a digit, not a spelled-out word, so this
# was not a corpus artifact but a real gap the field never exercised before.
_NUMBER_WORDS = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
                 "6": "six", "7": "seven", "8": "eight", "9": "nine",
                 "10": "ten", "11": "eleven", "12": "twelve"}


def _normalize_numerals(text: str) -> str:
    """Spell out small digit tokens so a numeral-rendered value can still land
    an exact match against a spelled-out allowed value ("1 pm" -> "one pm").
    "12 pm" folds to "twelve noon", matching the schema's own spelling rather
    than inventing a "twelve pm" the value set doesn't contain."""
    words = [_NUMBER_WORDS.get(w, w) for w in text.split()]
    normalized = " ".join(words)
    return normalized.replace("twelve pm", "twelve noon")


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
    cleaned = _normalize_numerals(cleaned)
    ranked = sorted(((v, phonetic_score(cleaned, v)) for v in values),
                    key=lambda p: p[1], reverse=True)
    return MatchResult(cleaned, cleaned in {v.lower() for v in values}, tuple(ranked))
