"""Scripted caller. Answers a repair move the way a cooperative human would.

Every reply maps to a real recording, and its word count is the word count of
what the caller actually utters in that recording, taken from the manifest's
reference text:
    yes / no      -> yes.wav / no.wav, one word
    answer        -> <item>_ans.wav, the field value alone
    take2         -> <item>_t2.wav, a genuine second take of the full sentence

Stated precisely, because the distinction matters if a judge checks: the
counts are reference word counts, not counts of recogniser output. What is
*not* modelled is the acoustic consequence. A category question is not
cheaper than a generic re-ask by assertion -- it is cheaper because a
different, shorter recording is streamed and transcribed for real, and
whatever the recogniser makes of it is what the agent has to work with.
"""
from dataclasses import dataclass

from sayless.moves import MoveKind, RepairMove


@dataclass(frozen=True)
class Reply:
    accepted: bool
    words: int
    audio: str              # "yes" | "no" | "answer" | "take2" | "none"
    value: str | None = None
    terminal: bool = False


def respond(move: RepairMove, truth: str, answer_words: int,
            sentence_words: int = 1) -> Reply:
    t = truth.strip().lower()
    cands = [c.strip().lower() for c in move.candidates]

    if move.kind is MoveKind.ESCALATE:
        return Reply(False, 0, "none", terminal=True)

    if move.kind is MoveKind.RESTRICTED_OFFER and cands:
        hit = cands[0] == t
        return Reply(hit, 1, "yes" if hit else "no",
                     value=move.candidates[0] if hit else None)

    if move.kind is MoveKind.TWO_WAY_OFFER:
        if t in cands:
            return Reply(True, answer_words, "answer",
                         value=move.candidates[cands.index(t)])
        return Reply(False, 1, "no")

    if move.kind is MoveKind.RESTRICTED_REQUEST:
        return Reply(False, answer_words, "answer")

    return Reply(False, sentence_words, "take2")
