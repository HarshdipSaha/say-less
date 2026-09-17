import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

import sys
ROOT = Path(r"H:\augsepthacks\assembly-ai hack")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
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

from eval_real_voice import REAL_MANIFEST, Transcriber, run_single

NOISY_DIR = ROOT / "corpus" / "noisy_audio"

async def main():
    tx = Transcriber(ROOT / "corpus" / "noisy_audio_transcript_cache.json")
    bcache = BinderCache(ROOT / "corpus" / "noisy_audio_binder_cache.json")
    log = DecisionLog(ROOT / "eval_decisions_noisy.jsonl")

    # Override audio paths in manifest to point to noisy audio
    NOISY_MANIFEST = []
    for item in REAL_MANIFEST:
        new_item = item.copy()
        new_item["id"] = item["id"] + "_noisy"
        new_item["audio"] = NOISY_DIR / item["audio"].name
        NOISY_MANIFEST.append(new_item)

    print(f"Running Noisy Real Voice Evaluation on {len(NOISY_MANIFEST)} items...")
    
    base_records = []
    print("\n--- Running Baseline Arm on Noisy Voice ---")
    for item in NOISY_MANIFEST:
        rec = await run_single(item, plan_repair_baseline, "baseline", tx, bcache, log)
        base_records.append(rec)
        print(f"  [Baseline] {item['id']:<15} -> committed: {rec.committed!r:<15} turns: {rec.turns} words_resaid: {rec.repair_words}")

    sayless_records = []
    print("\n--- Running Say Less Arm on Noisy Voice ---")
    for item in NOISY_MANIFEST:
        rec = await run_single(item, plan_repair, "sayless", tx, bcache, log)
        sayless_records.append(rec)
        print(f"  [Say Less] {item['id']:<15} -> committed: {rec.committed!r:<15} turns: {rec.turns} words_resaid: {rec.repair_words}")

    tx.save()
    bcache.save()

    b_agg = aggregate(base_records)
    s_agg = aggregate(sayless_records)

    print("\n=======================================================")
    print("        NOISY REAL HUMAN VOICE EVALUATION RESULTS      ")
    print("=======================================================")
    print(table(b_agg, s_agg))
    print("=======================================================")

    results = {
        "dataset": "Appointment-Bench (Samsung S23 + iPhone 16 Pro) Noisy + SLURP",
        "item_count": len(NOISY_MANIFEST),
        "baseline": b_agg,
        "sayless": s_agg,
        "records": {
            "baseline": [r.__dict__ for r in base_records],
            "sayless": [r.__dict__ for r in sayless_records]
        }
    }
    (ROOT / "eval_results_noisy.json").write_text(json.dumps(results, indent=2))
    print(f"Results saved to {ROOT / 'eval_results_noisy.json'}")

if __name__ == "__main__":
    asyncio.run(main())
