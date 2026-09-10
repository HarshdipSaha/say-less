"""Download SLURP far-field audio and build a manifest for bounded fields.

Audio is CC BY-NC 4.0. It is never committed; corpus/audio/ is gitignored.
Attribution belongs in the README.

Not run for this submission: the plan's own default expectation (Task 14)
is that this is skipped given the schedule, and the self-recorded (here:
synthesized) corpus carries the evaluation instead. Left as a stub so the
integration path is documented rather than silently absent.
"""
import sys

SLURP_REPO = "https://github.com/pswietojanski/slurp"
print(f"Fetch SLURP metadata and audio from {SLURP_REPO}; audio lives on Zenodo (~6 GB).")
print("Select utterances whose annotated entity is a date, a time or a person name,")
print("take the far-field (no -headset suffix) recording, and emit corpus/manifest_slurp.json")
print("in the same shape as corpus/manifest.json, including slot_span. Keep the headset")
print("version of the same utterance as the easy-condition control. SLURP has no second")
print("take and no answer-only clip, so either record substitutes or restrict the SLURP arm")
print("to reporting commit accuracy alone.")
sys.exit(0)
