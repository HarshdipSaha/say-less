"""Turn evidence assembled from Universal-Streaming Turn frames."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WordEvidence:
    text: str
    start_ms: int
    end_ms: int
    confidence: float
    is_final: bool
    revisions: int          # times this position's text changed across partials


@dataclass(frozen=True)
class TurnEvidence:
    turn_order: int
    transcript: str
    end_of_turn_confidence: float
    words: tuple[WordEvidence, ...]

    def min_confidence(self, indices: tuple[int, ...]) -> float:
        return min((self.words[i].confidence for i in indices), default=1.0)


@dataclass(frozen=True)
class BoundField:
    """A schema field, the text heard for it, and the words that produced it."""
    field: str
    heard_value: str
    word_indices: tuple[int, ...]


class TurnAccumulator:
    """Feed every Turn frame in. Returns a TurnEvidence when a turn finalises."""

    def __init__(self) -> None:
        self._order: int | None = None
        self._seen: list[str] = []
        self._revisions: list[int] = []

    def _reset(self, order: int) -> None:
        self._order, self._seen, self._revisions = order, [], []

    def push(self, frame: dict) -> TurnEvidence | None:
        if frame.get("type") != "Turn":
            return None
        order = frame.get("turn_order", 0)
        if order != self._order:
            self._reset(order)

        raw = frame.get("words") or []
        for i, w in enumerate(raw):
            text = w.get("text", "")
            if i >= len(self._seen):
                self._seen.append(text)
                self._revisions.append(0)
            elif self._seen[i] != text:
                self._seen[i] = text
                self._revisions[i] += 1

        if not frame.get("end_of_turn"):
            return None

        words = tuple(
            WordEvidence(
                text=w.get("text", ""),
                start_ms=int(w.get("start", 0)),
                end_ms=int(w.get("end", 0)),
                confidence=float(w.get("confidence", 0.0)),
                is_final=bool(w.get("word_is_final", False)),
                revisions=self._revisions[i] if i < len(self._revisions) else 0,
            )
            for i, w in enumerate(raw)
        )
        turn = TurnEvidence(order, frame.get("transcript", ""),
                            float(frame.get("end_of_turn_confidence", 0.0)), words)
        self._reset(order + 1)
        return turn
