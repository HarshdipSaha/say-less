import json
from pathlib import Path
from sayless.evidence import TurnAccumulator

FIX = Path(__file__).parent / "fixtures" / "turn_frames_day01.json"


def test_accumulator_yields_one_turn_per_end_of_turn():
    frames = json.loads(FIX.read_text())
    acc = TurnAccumulator()
    turns = [t for f in frames if (t := acc.push(f)) is not None]
    assert len(turns) == sum(1 for f in frames if f.get("end_of_turn"))


def test_turn_carries_words_and_end_of_turn_confidence():
    frames = json.loads(FIX.read_text())
    acc = TurnAccumulator()
    turn = [t for f in frames if (t := acc.push(f)) is not None][-1]
    assert turn.words and turn.transcript
    assert 0.0 <= turn.end_of_turn_confidence <= 1.0
    assert all(0.0 <= w.confidence <= 1.0 for w in turn.words)


def test_revision_count_tracks_positions_that_changed():
    acc = TurnAccumulator()
    acc.push({"type": "Turn", "turn_order": 0, "end_of_turn": False,
              "transcript": "book tuesday", "end_of_turn_confidence": 0.1,
              "words": [{"text": "book", "start": 0, "end": 100, "confidence": 0.9, "word_is_final": True},
                        {"text": "tuesday", "start": 100, "end": 300, "confidence": 0.4, "word_is_final": False}]})
    turn = acc.push({"type": "Turn", "turn_order": 0, "end_of_turn": True,
                     "transcript": "book thursday", "end_of_turn_confidence": 0.9,
                     "words": [{"text": "book", "start": 0, "end": 100, "confidence": 0.9, "word_is_final": True},
                               {"text": "thursday", "start": 100, "end": 300, "confidence": 0.5, "word_is_final": True}]})
    assert turn.words[0].revisions == 0
    assert turn.words[1].revisions == 1
