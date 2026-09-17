"""Run A/B evaluation on real human voice audio from Appointment-Bench & SLURP."""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import sys
ROOT = Path(r"H:\augsepthacks\assembly-ai hack")
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from sayless.baseline import plan_repair_baseline
from sayless.binder import BinderCache, bind
from sayless.decisionlog import DecisionLog
from sayless.matcher import match
from sayless.planner import RepairState, plan_after_rejection, plan_repair
from sayless.schema import BOOKING_SCHEMA
from sayless.stream import TranscriptCache, transcribe_file
from evalharness.metrics import RunRecord, aggregate, table
from evalharness.simulator import respond

class Transcriber:
    def __init__(self, path: Path, offline: bool = False) -> None:
        self.cache = TranscriptCache(path)
        self.offline = offline
        self.misses = 0

    async def get(self, audio: Path, keyterms: list[str] | None):
        hit, turn = self.cache.get(audio, keyterms)
        if hit:
            return turn
        self.misses += 1
        if self.offline:
            raise RuntimeError(f"Missing cache for {audio.name}")
        print(f"    [Streaming API call] {audio.name}...")
        turn = await transcribe_file(audio, keyterms)
        self.cache.put(audio, keyterms, turn)
        self.cache.save()
        return turn

    def save(self) -> None:
        self.cache.save()

REAL_MANIFEST = [
    # 1. Person 1 (Ethiopian accent, Samsung Galaxy S23, outdoor playground)
    {
        "id": "real_p1_thu",
        "field": "day",
        "truth": "Thursday",
        "sentence": "Can we do both on Thursday?",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p1_t01.wav",
        "answer": ROOT / "corpus" / "audio" / "day_04_ans.wav"
    },
    {
        "id": "real_p1_mon",
        "field": "day",
        "truth": "Monday",
        "sentence": "Monday's fine. I need morning for my cleaning.",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p1_t03.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    {
        "id": "real_p1_mon2",
        "field": "day",
        "truth": "Monday",
        "sentence": "Let's book mine first the Monday morning cleaning.",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p1_t10.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    # 2. Person 2 (American accent, iPhone 16 Pro, outdoor park)
    {
        "id": "real_p2_thu",
        "field": "day",
        "truth": "Thursday",
        "sentence": "Can we do both on Thursday?",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p2_t01.wav",
        "answer": ROOT / "corpus" / "audio" / "day_04_ans.wav"
    },
    {
        "id": "real_p2_mon",
        "field": "day",
        "truth": "Monday",
        "sentence": "Monday's fine. I need morning for my cleaning.",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p2_t03.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    {
        "id": "real_p2_mon2",
        "field": "day",
        "truth": "Monday",
        "sentence": "Let's book mine first the Monday morning cleaning.",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p2_t10.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    # 3. SLURP Natural Voice (diverse speakers & environments)
    {
        "id": "real_slurp_tue",
        "field": "day",
        "truth": "Tuesday",
        "sentence": "weather on tuesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_tue_2158.wav",
        "answer": ROOT / "corpus" / "audio" / "day_01_ans.wav"
    },
    {
        "id": "real_slurp_wed",
        "field": "day",
        "truth": "Wednesday",
        "sentence": "turn off the six am alarm for wednesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_wed_0895.wav",
        "answer": ROOT / "corpus" / "audio" / "day_03_ans.wav"
    },
    # 4. Benchmark expansion (2026-09-17): the 4 real ab_p1/ab_p2 takes not
    # already in the manifest (t05, t08) turned out NOT to be day-field
    # content once actually transcribed -- t08 for both speakers ("Last name
    # for both is Nolan...") names a surname outside this project's own
    # 319-name corpus/surnames.txt, which would test "value can never resolve
    # in-set" rather than the mishearing-recovery this manifest otherwise
    # measures, so it's left out. ab_p1_t05 was tried and dropped too: a fresh
    # live transcribe_file() call returned only "keep mixing them up." --
    # transcribe_file() returns just the LAST finalised turn, and this
    # specific recording's mid-sentence pause made AssemblyAI's turn detector
    # split it, silently losing the earlier content. That's a real property of
    # the offline one-shot replay helper the eval scripts use, not of the live
    # per-turn path (session.py's BookingSession.handle_turn processes every
    # finalised Turn as it arrives), so it wasn't treated as a src/sayless bug
    # to fix -- see docs/STATUS.md's decision log. Only ab_p2_t05 was usable,
    # and it happens to name a real *service* ("consultation"), so it's the
    # manifest's only non-day/time real item. It needed its own answer clip:
    # corpus/audio's five svc_XX_ans.wav files are beard trim/haircut/hot
    # towel shave/head massage/kids cut -- none say "consultation" -- so
    # corpus/audio/svc_consultation_ans.wav was synthesized the same way
    # (Windows SAPI "David", narrowband round-trip + 14-20dB noise) rather
    # than reusing a mismatched clip.
    {
        "id": "real_p2_consult",
        "field": "service",
        "truth": "consultation",
        "sentence": "Wait for Danielle's consultation.",
        "audio": ROOT / "corpus" / "real_audio" / "ab_p2_t05.wav",
        "answer": ROOT / "corpus" / "audio" / "svc_consultation_ans.wav"
    },
    # 5. SLURP-sourced day/time clips (2026-09-17), pulled individually via the
    # qmeeus/slurp Hugging Face mirror's datasets-server /rows endpoint (no
    # bulk download): candidates were selected offline from the corpus/slurp
    # annotation clone (wer 0.0 recordings, short single-entity sentences),
    # then each row's exact offset was computed from local jsonl order
    # (verified against the two pre-existing SLURP items before trusting it)
    # so no flaky /search or /filter call was needed. Two per day for all
    # seven days, plus three `time` items -- the first field besides `day`
    # this real-voice manifest has ever covered. corpus/audio had no Saturday
    # or Sunday answer clip and no `time` answer clips at all, so
    # day_saturday_ans.wav, day_sunday_ans.wav and the three time_*_ans.wav
    # files were synthesized the same way as svc_consultation_ans.wav above.
    #
    # Four other downloaded candidates were transcribed and discarded, not
    # used: two came back from the real API as unrelated garbled text with no
    # day/time word in it at all (a genuine real-audio clarity limit, not a
    # pipeline bug), and one ("is my calendar free for thursday") was heard by
    # AssemblyAI as "Tuesday" with 1.0 confidence -- a real mishearing, but
    # ambiguous enough (own-recording vs. genuine ASR error) that it was
    # swapped for a cleaner Thursday clip rather than risk a misleading
    # ground-truth label. See docs/STATUS.md's decision log.
    {
        "id": "real_slurp_sun1",
        "field": "day",
        "truth": "Sunday",
        "sentence": "sunday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_sun_0327.wav",
        "answer": ROOT / "corpus" / "audio" / "day_sunday_ans.wav"
    },
    {
        "id": "real_slurp_sun2",
        "field": "day",
        "truth": "Sunday",
        "sentence": "please delete all reminder of sunday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_sun_8863.wav",
        "answer": ROOT / "corpus" / "audio" / "day_sunday_ans.wav"
    },
    {
        "id": "real_slurp_mon1",
        "field": "day",
        "truth": "Monday",
        "sentence": "remind me before monday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_mon_7454.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    {
        "id": "real_slurp_mon2",
        "field": "day",
        "truth": "Monday",
        "sentence": "remove the event from monday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_mon_7913.wav",
        "answer": ROOT / "corpus" / "audio" / "day_02_ans.wav"
    },
    {
        "id": "real_slurp_tue2",
        "field": "day",
        "truth": "Tuesday",
        "sentence": "remind it on tuesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_tue_7084.wav",
        "answer": ROOT / "corpus" / "audio" / "day_01_ans.wav"
    },
    {
        "id": "real_slurp_tue3",
        "field": "day",
        "truth": "Tuesday",
        "sentence": "please check weather on tuesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_tue_5377.wav",
        "answer": ROOT / "corpus" / "audio" / "day_01_ans.wav"
    },
    {
        "id": "real_slurp_wed2",
        "field": "day",
        "truth": "Wednesday",
        "sentence": "is it wednesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_wed_8343.wav",
        "answer": ROOT / "corpus" / "audio" / "day_03_ans.wav"
    },
    {
        "id": "real_slurp_wed3",
        "field": "day",
        "truth": "Wednesday",
        "sentence": "what's the weather next wednesday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_wed_6411.wav",
        "answer": ROOT / "corpus" / "audio" / "day_03_ans.wav"
    },
    {
        "id": "real_slurp_thu1",
        "field": "day",
        "truth": "Thursday",
        "sentence": "what alarms do i have set for thursday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_thu_1037.wav",
        "answer": ROOT / "corpus" / "audio" / "day_04_ans.wav"
    },
    {
        "id": "real_slurp_thu2",
        "field": "day",
        "truth": "Thursday",
        "sentence": "tell me what's happening next thursday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_thu_8348.wav",
        "answer": ROOT / "corpus" / "audio" / "day_04_ans.wav"
    },
    {
        "id": "real_slurp_fri1",
        "field": "day",
        "truth": "Friday",
        "sentence": "is it friday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_fri_6926.wav",
        "answer": ROOT / "corpus" / "audio" / "day_05_ans.wav"
    },
    {
        "id": "real_slurp_fri2",
        "field": "day",
        "truth": "Friday",
        "sentence": "set an event for friday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_fri_6774.wav",
        "answer": ROOT / "corpus" / "audio" / "day_05_ans.wav"
    },
    {
        "id": "real_slurp_sat1",
        "field": "day",
        "truth": "Saturday",
        "sentence": "clear my calendar for saturday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_sat_7741.wav",
        "answer": ROOT / "corpus" / "audio" / "day_saturday_ans.wav"
    },
    {
        "id": "real_slurp_sat2",
        "field": "day",
        "truth": "Saturday",
        "sentence": "what is the date next saturday",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_sat_5483.wav",
        "answer": ROOT / "corpus" / "audio" / "day_saturday_ans.wav"
    },
    {
        "id": "real_slurp_time_onepm",
        "field": "time",
        "truth": "one pm",
        "sentence": "set an alarm for one pm",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_time_538.wav",
        "answer": ROOT / "corpus" / "audio" / "time_one_pm_ans.wav"
    },
    {
        "id": "real_slurp_time_threepm",
        "field": "time",
        "truth": "three pm",
        "sentence": "disable alarm for three pm",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_time_1205.wav",
        "answer": ROOT / "corpus" / "audio" / "time_three_pm_ans.wav"
    },
    {
        "id": "real_slurp_time_nineam",
        "field": "time",
        "truth": "nine am",
        "sentence": "clear my nine am alarms",
        "audio": ROOT / "corpus" / "real_audio" / "slurp_time_3153.wav",
        "answer": ROOT / "corpus" / "audio" / "time_nine_am_ans.wav"
    }
]

async def run_single(item, planner, arm, tx, bcache, log):
    spec = BOOKING_SCHEMA[item["field"]]
    truth = item["truth"]
    answer_words = len(truth.split())
    sentence_words = len(item["sentence"].split())

    state = RepairState()
    audio = item["audio"]
    keyterms = None
    repair_words = turns = 0
    committed, in_set, confident, escalated = None, False, False, False
    pending_offer = None

    for _ in range(5):
        turns += 1
        turn = await tx.get(audio, keyterms)
        if turn is None:
            break

        if pending_offer is not None:
            fields = []
            move = plan_after_rejection(item["field"], spec, state)
            pending_offer = None
        else:
            fields = bind(turn.transcript, [w.text for w in turn.words],
                          BOOKING_SCHEMA, bcache, offline=False)
            target_fields = [f for f in fields if f.field == item["field"]]
            move = planner(turn, target_fields, BOOKING_SCHEMA, state)
        log.write(arm, item["id"], turn, fields, move)

        if move is None:
            bf = next((b for b in fields if b.field == item["field"]), None)
            if bf:
                m = match(bf.heard_value, spec.values)
                in_set = m.in_set
                confident = turn.min_confidence(bf.word_indices) >= spec.confidence_threshold if bf.word_indices else True
                committed = (next((v for v in spec.values if v.lower() == m.heard.lower()), None)
                             if in_set else bf.heard_value)
            break

        state.record(move)
        state.new_turn()
        reply = respond(move, truth, answer_words, sentence_words)
        repair_words += reply.words

        if reply.terminal:
            escalated = True
            break
        if reply.accepted:
            committed = reply.value or committed
            in_set = True
            confident = True
            break

        if reply.audio == "no":
            pending_offer = move.candidates[0] if move.candidates else None
            audio = ROOT / "corpus" / "audio" / "no.wav"
            continue

        audio = item["answer"] if reply.audio == "answer" else item["audio"]

    return RunRecord(item["id"], item["field"], truth, committed, turns,
                     repair_words, in_set, confident, escalated)

async def main():
    tx = Transcriber(ROOT / "corpus" / "real_audio_transcript_cache.json")
    bcache = BinderCache(ROOT / "corpus" / "real_audio_binder_cache.json")
    log = DecisionLog(ROOT / "eval_decisions_real.jsonl")

    print(f"Running Real Voice Evaluation on {len(REAL_MANIFEST)} items...")
    
    base_records = []
    print("\n--- Running Baseline Arm on Real Voice ---")
    for item in REAL_MANIFEST:
        rec = await run_single(item, plan_repair_baseline, "baseline", tx, bcache, log)
        base_records.append(rec)
        print(f"  [Baseline] {item['id']:<15} -> committed: {rec.committed!r:<15} turns: {rec.turns} words_resaid: {rec.repair_words}")

    sayless_records = []
    print("\n--- Running Say Less Arm on Real Voice ---")
    for item in REAL_MANIFEST:
        rec = await run_single(item, plan_repair, "sayless", tx, bcache, log)
        sayless_records.append(rec)
        print(f"  [Say Less] {item['id']:<15} -> committed: {rec.committed!r:<15} turns: {rec.turns} words_resaid: {rec.repair_words}")

    tx.save()
    bcache.save()

    b_agg = aggregate(base_records)
    s_agg = aggregate(sayless_records)

    print("\n=======================================================")
    print("        REAL HUMAN VOICE EVALUATION RESULTS            ")
    print("=======================================================")
    print(table(b_agg, s_agg))
    print("=======================================================")

    results = {
        "dataset": "Appointment-Bench (Samsung S23 + iPhone 16 Pro) & SLURP",
        "item_count": len(REAL_MANIFEST),
        "baseline": b_agg,
        "sayless": s_agg,
        "records": {
            "baseline": [r.__dict__ for r in base_records],
            "sayless": [r.__dict__ for r in sayless_records]
        }
    }
    (ROOT / "eval_results_real.json").write_text(json.dumps(results, indent=2))
    print(f"Results saved to {ROOT / 'eval_results_real.json'}")

if __name__ == "__main__":
    asyncio.run(main())
