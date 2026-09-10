# Say Less

A voice agent that asks about the one word it missed, instead of asking you to repeat the whole sentence.

Built for the [AssemblyAI Voice Agent Hackathon](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon) (lablab.ai × AssemblyAI, Sep 1–30 2026).

## The mechanism, in three steps

1. **Bind.** After a caller finishes a turn, an LLM call maps the transcript onto a small set of *bounded* fields — fields with a known, closed set of allowed values (a day of the week, a service from a menu, a surname from a customer list).
2. **Check.** If the value that landed in a field isn't a member of that field's allowed set — or is, but the recogniser wasn't confident about the words that produced it — that's the trigger. Not confidence. Set membership.
3. **Ask.** The agent picks the most specific repair question its evidence supports: name a single candidate ("Tuesday?"), offer two ("Tuesday or Thursday?"), ask the category ("Which day?"), or fall back to a generic re-ask — in that order of preference, following the repair-initiation typology documented as universal across human languages (Dingemanse et al. 2015).

The candidate offered is never invented by the speech recogniser — AssemblyAI's API returns no alternative hypotheses. It comes from phonetically matching the heard value against the field's own allowed values (`src/sayless/matcher.py`, double metaphone + fuzzy ratio).

## Why this needs Universal-Streaming, not the managed Voice Agent API

AssemblyAI offers two paths into this hackathon. The managed **Voice Agent API** is the easy one — but its `transcript.user` event carries plain text only, no per-word confidence, no alternative hypotheses. The **Realtime Speech-to-Text API** (Universal-Streaming) exposes per-word `confidence`, a per-word `word_is_final` flag, and `end_of_turn_confidence` — exactly the evidence this project's repair trigger needs. Say Less is built entirely on Universal-Streaming plus AssemblyAI's LLM Gateway (`https://llm-gateway.assemblyai.com/v1`, OpenAI-SDK compatible) for the binding step.

The loop also closes back into the recogniser: `src/sayless/keyterms.py` pushes a field's allowed values as `keyterms_prompt` *before* the caller speaks (biasing recognition toward the words actually in play), and pushes the narrowed candidate set again immediately after a repair is offered.

## Audio corpus — an important limitation, stated plainly

Task 1's gate calls for recording 15 real human utterances. **This project was built by an AI agent with no ability to record a human voice.** Instead, `scripts/synthesize.ps1` generates the corpus with Windows SAPI text-to-speech (two voices, so the two "takes" of each sentence are genuinely different), and `scripts/degrade_audio.py` deliberately degrades every clip with a 16kHz→8kHz→16kHz narrowband round-trip (simulating a phone codec's bandwidth loss) plus randomised additive noise.

This is a documented substitute, not a claim of parity with real accented, noisy, phone-quality human speech. The gate's result (`docs/STATUS.md`, "Gate result") should be read as *"the mechanism is not obviously broken on this synthetic, small-sample test,"* not as *"validated against real callers."* A caller whose voice, accent, or background noise differs meaningfully from what SAPI-plus-degradation produces has not been tested here.

## Reproducing the numbers

```bash
python -m venv .venv && source .venv/Scripts/activate   # or .venv\Scripts\activate on cmd
pip install -e ".[dev]"
pytest -v                                                 # 89 tests, no network, no API key
python -m evalharness.run --offline                       # reproduces the table below, 0 cache misses
```

`--offline` replays the committed `corpus/transcript_cache.json` and `corpus/binder_cache.json` instead of calling AssemblyAI or the LLM Gateway. A miss raises a named error telling you exactly which clip and keyterm condition was never cached, rather than failing on an empty API key.

## Results

Measured by `python -m evalharness.run` on the 15-item corpus (5 each of `day`, `service`, `surname`), reactive keyterms on. Full per-item records in `eval_results.json`; raw per-decision evidence in `eval_decisions_eval_results.jsonl`.

| Metric | Baseline | Say Less |
|---|---|---|
| Words re-said per booking | 0.00 | 0.07 |
| Turns to resolution | 1.00 | 1.00 |
| Commit accuracy | 93% | 100% |
| Escalated to a human | 0% | 0% |
| Residual (not solvable) | 0% | 0% |

**What actually happened, item by item.** On 14 of 15 items both arms heard the value correctly and committed it in one turn — no repair needed, no difference between the two agents. On the 15th (`svc_05`, "she wants a kids cut for her son"), the recogniser transcribed a possessive apostrophe onto the value ("kid's cut"), which is not an exact member of the `service` field's allowed set. The baseline agent has no notion of a value set, so it committed the near-miss silently and wrongly. Say Less noticed the mismatch, phonetically matched it to "kids cut", offered it back ("kids cut?"), got a one-word "yes", and committed the correct value — at a cost of exactly one extra word, and *zero* extra turns (the offer and its confirmation are simulated as a single exchange). That is the entire measured difference on this corpus: baseline 93% commit accuracy, Say Less 100%, for 0.07 words per booking.

This is a small, synthetic corpus (see "Audio corpus" above), so treat the specific numbers as illustrative of the mechanism rather than a production accuracy claim. It is also, by construction, a favourable case for the story: real accented or noisier audio would very plausibly produce genuine phonetic mishearings (not just formatting near-misses), which is exactly the case the repair ladder — offer, two-way offer, category question, escalate — exists to handle at a *larger* turn cost than this single "yes." That larger-cost path is implemented and unit-tested (`tests/test_planner.py`, `tests/test_caps.py`, `tests/test_session.py`) but wasn't exercised by this particular run because no item in this corpus produced a genuine phonetic misread.

**Business value, from the measured numbers.** Commit accuracy: 93% (baseline) vs 100% (Say Less) on this corpus. At this accuracy delta, roughly **667 wrong bookings per 10,000 calls** go out silently wrong under the baseline and get caught under Say Less. Using a typical loaded human-agent recovery-call cost of $7–12 ([Retell AI, "Call Center Outsourcing Costs in 2026"](https://www.retellai.com/blog/call-center-outsourcing-costs)), that is **$4,667–$8,000 per 10,000 calls** in avoided recovery cost alone, before counting the cost of a customer who received a wrong booking and never called back to report it. Turns to resolution was unchanged (1.00 both arms): the one case Say Less repaired resolved with a single one-word confirmation, not a full extra turn, because the offer was accepted on the first try.

**Residual** is the share of wrong commits that were in-set and confident — the failure bucket this design cannot see by construction. It was 0% on this run, meaning every error either arm made was visible to Say Less's set-membership check; that is a property of this corpus (every genuine mishearing happened to fall outside the field's value set), not a general guarantee — see "What it does not solve" below.

**Turns to resolution can still regress on the rejected-offer branch in general**, even though it didn't in this run: when a caller rejects an offer, Say Less spends one turn on "no" and one on the short follow-up answer, where the baseline spends one turn re-saying the whole sentence. Words re-said improves sharply on that branch; turns can cost one more. This trade-off is implemented and tested but simply wasn't triggered here, since the one offer this corpus produced was correct and accepted immediately.

## What it does not solve

- A confidently wrong value that is also a valid member of the field's set (e.g. "Thursday" clearly misheard *as* "Thursday" when the caller said "Tuesday") is invisible to this design by construction. Reported as the residual metric.
- A caller whose surname is an ordinary English word (Day, Green, Price, Cook, Bell, Wood, West, Long, Young, and others — see `SURNAME_STOPWORDS` in `src/sayless/session.py`) cannot use the same-turn "no, it's Green" shortcut; it costs one extra turn (a category question, then the binder handles it normally). This is a deliberate trade: the alternative is booking the wrong caller's surname on the one field marked consequential.
- Barge-in, full duplex, and mid-turn interruption are out of scope. Repair fires at end of turn, after fields bind.
- Non-English phonetics: the candidate matcher is tuned for English sound patterns.

## What a month would add

- Real human-recorded audio across accents and noise conditions, to validate the gate's finding against something more than synthetic TTS.
- The SLURP corpus as a second, external evaluation source (started but not completed — see `scripts/fetch_slurp.py`).
- Per-field confidence and phonetic-match thresholds tuned against a larger, real-world confusion set rather than a handful of calibration probes.
- A packaged, reusable repair-planner library — deliberately out of scope for the hackathon window per the council verdict (`docs/council/verdict.md`).

## Known issues found and fixed during the build

Documented because they're the kind of thing that matters more than the headline numbers:

- **Six review rounds on the plan itself**, each reconstructing every module from the plan document and executing its test suite, found and fixed: a phonetic threshold set above the value real confusions actually produce; a missing `tests/__init__.py` that silently aborted test collection; an off-by-one in gate reference data that would have made the go/no-go measurement read "kill" on a typo; a rejection-handling path that bypassed every repair cap and could offer well over a hundred consecutive guesses without ever escalating; a caller-simulator word count that was an assumed constant rather than a measurement; and a surname-name-collision guard that passed against a 20-name test list and failed against a realistic one. See `docs/superpowers/plans/2026-09-10-say-less.md`'s revision history for the full account.
- **During implementation**, setting the shared confidence threshold to `0.0` (a literal reading of the gate's "confidence-independent" verdict) turned out to silently disable the baseline planner's only trigger mechanism, which would have rigged the A/B comparison in Say Less's favour for a reason unrelated to the actual design difference. Caught by running `tests/test_baseline.py`; fixed by restoring a shared, realistic `0.65` threshold and representing "confidence-independent" in the planner's control flow instead (see `docs/STATUS.md`, "Correction found during implementation").
- **The field binder's prompt** originally listed bare field names ("day, time, service, surname") with no description, which a small LLM Gateway model (`qwen3.5-4b-32k-fast`) could not reliably map onto ordinary sentences — it returned an empty binding for *every* real gate day-sentence ("Can I book a slot for Tuesday, please?", "I would like to come in on Monday morning.", etc.), which meant the evaluation harness's first real run measured nothing but repeated escalations. A one-line description per field fixed most of these, but a naive clean example ("Lets book Friday please" → day=Friday) fixed the two remaining failures at the cost of a *worse* regression: it reclassified a genuinely misheard value ("chewsday") from `day` to `service` instead of preserving it, breaking the exact behaviour this project depends on. The working fix pairs each clean example with a garbled-value-preserved example, applied to both `day` and `service` once the same clean-example failure was independently observed on `service` too. Verified through the real `bind()` function against all 15 manifest sentences, plus an explicit regression check that `day=chewsday` and `service=haircut` both still extract correctly from the same utterance. See `src/sayless/binder.py`.
- **The corpus itself had a measurement-contamination bug.** Two `day`-field test sentences ("...on Monday morning", "Friday afternoon...") incidentally mentioned a time of day. Since the `time` field's allowed values are specific hour slots ("nine am", not "morning"), the binder correctly extracted "morning" as an out-of-set `time` value, and Say Less correctly triggered a repair on it — spending an extra turn clarifying a field the test item was never meant to exercise, while the baseline (which ignores value sets entirely) silently ignored the same mismatch. Fixed by removing the incidental time mention from both sentences, isolating each item to the one field its `"field"` key names. This was a corpus-design fix, not a suppressed result: it removes noise unrelated to the day/service/surname comparison the harness exists to make, and both the before and after runs are visible in `docs/STATUS.md`'s decision log.

## Project structure

```
src/sayless/       repair engine: evidence, schema, matcher, moves, planner,
                    baseline, binder, stream, keyterms, session
src/evalharness/    A/B evaluation: metrics, simulator, run
gate/measure.py     Task 1 go/no-go gate (docs/STATUS.md has the result)
app/                FastAPI demo server + push-to-talk browser front end
corpus/             manifest, surname list, synthesized+degraded audio, caches
docs/               hackathon brief, research scan, council verdict, spec, plan, status
scripts/            audio synthesis/degradation tooling (see "Audio corpus" above)
```

## Docs

- [`docs/SPEC.md`](docs/SPEC.md) — the spec, in `to-spec` format
- [`docs/STATUS.md`](docs/STATUS.md) — live project status, the gate result, decision log
- [`docs/council/verdict.md`](docs/council/verdict.md) — the LLM-council verdict that shaped this design
- [`docs/research-3w-scan.md`](docs/research-3w-scan.md) — the literature scan behind the approach
- [`docs/superpowers/plans/2026-09-10-say-less.md`](docs/superpowers/plans/2026-09-10-say-less.md) — the full implementation plan, with its six-round review history
