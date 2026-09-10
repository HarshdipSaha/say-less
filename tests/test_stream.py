import json
from pathlib import Path
from sayless.stream import replay_frames

FIX = Path(__file__).parent / "fixtures" / "turn_frames_day01.json"


def test_replay_yields_turn_evidence_offline():
    turns = list(replay_frames(json.loads(FIX.read_text())))
    assert turns and turns[-1].transcript
