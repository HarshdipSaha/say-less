"""One JSONL line per planner decision, with the evidence that produced it."""
import json
from pathlib import Path

from .evidence import BoundField, TurnEvidence
from .moves import RepairMove


class DecisionLog:
    def __init__(self, path: Path | None) -> None:
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("")

    def write(self, arm: str, item: str, turn: TurnEvidence,
              fields: list[BoundField], move: RepairMove | None) -> None:
        if not self.path:
            return
        row = {
            "arm": arm, "item": item, "transcript": turn.transcript,
            "end_of_turn_confidence": turn.end_of_turn_confidence,
            "words": [{"t": w.text, "c": round(w.confidence, 3), "r": w.revisions}
                      for w in turn.words],
            "bound": [{"field": b.field, "heard": b.heard_value,
                       "idx": list(b.word_indices)} for b in fields],
            "move": move.kind.label if move else "accept",
            "candidates": list(move.candidates) if move else [],
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
