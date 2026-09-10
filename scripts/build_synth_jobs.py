"""Build the list of TTS synthesis jobs for the gate corpus.

Say Less's gate (docs/superpowers/plans/2026-09-10-say-less.md, Task 1) calls
for recording 15 human utterances. No human voice was available to this
builder, so the corpus is synthesized instead with Windows SAPI (David and
Zira voices) and then acoustically degraded (scripts/degrade_audio.py) to
approximate a hard phone call. This is a documented substitute, not the
literal plan step -- see the "Audio corpus" section of the README.

This script only decides WHAT to synthesize (text, voice, rate) for each of
the 47 clips the manifest needs. It does not touch audio.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "corpus" / "manifest.json").read_text())

jobs = []
for item in manifest["items"]:
    jobs.append({"out": f"{item['id']}_t1", "text": item["sentence"],
                 "voice": "David", "rate": 0})
    jobs.append({"out": f"{item['id']}_t2", "text": item["sentence"],
                 "voice": "Zira", "rate": -1})
    jobs.append({"out": f"{item['id']}_ans", "text": item["truth"],
                 "voice": "David", "rate": 0})

jobs.append({"out": "yes", "text": "yes", "voice": "David", "rate": 0})
jobs.append({"out": "no", "text": "no", "voice": "David", "rate": 0})

out = ROOT / "gate" / "synth_jobs.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(jobs, indent=2))
print(f"wrote {len(jobs)} jobs to {out}")
