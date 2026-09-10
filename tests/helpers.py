"""Builders shared across test modules."""
from sayless.evidence import BoundField, TurnEvidence, WordEvidence


def turn(words, eot=0.9, transcript="x"):
    """words is a list of (text, confidence) pairs."""
    return TurnEvidence(
        turn_order=0, transcript=transcript, end_of_turn_confidence=eot,
        words=tuple(WordEvidence(t, 0, 100, c, True, 0) for t, c in words),
    )


def bound(field, value, idx):
    return BoundField(field=field, heard_value=value, word_indices=(idx,))
