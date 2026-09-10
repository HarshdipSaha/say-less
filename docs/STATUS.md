# STATUS — AssemblyAI Voice Agent Hackathon (Sep 1–30, 2026)

Project: **Say Less** — repair for bounded slots in voice agents.
Last updated: 2026-09-11 (implementation in progress: Tasks 0-18 built and committed; evaluation run pending a clean pass).
Repo: **https://github.com/HarshdipSaha/say-less**
Spec: `docs/SPEC.md` · Plan: `docs/superpowers/plans/2026-09-10-say-less.md` · Council verdict: `docs/council/verdict.md` · Transcript: `docs/council/transcript.md` · Research: `docs/research-3w-scan.md` · Brief: `docs/hackathon-brief.md`

**Deadline: Sep 30, 2026, 8:30 PM IST. Target submission date: Sep 28.** 18 days remain; ~20 evenings of capacity assumed (solo, evenings and weekends).

---

## Where we are

| Phase | State | Notes |
|---|---|---|
| Understand hackathon | DONE | Full page captured via Playwright into `hackathon-brief.md`: two build paths, prizes, judging criteria, submission requirements, schedule, judge list, and a themed survey of ~35 already-submitted competitors |
| Research — literature | DONE | arXiv sweep across six angles; WHY/HOW/WHAT scan of five papers in `research-3w-scan.md`. Gap identified: agent-side repair-format selection is unoccupied |
| Research — market | DONE | Production failure-mode study (10M+ minutes), contact-centre containment and cost-per-call figures, voice-AI share of inbound volume |
| Research — API feasibility | DONE | Universal-Streaming exposes per-word `confidence`, `word_is_final`, `end_of_turn_confidence`. Voice Agent API exposes plain text only. **No N-best anywhere.** Keyterms Prompting: 100 terms, mid-session updatable. LLM Gateway is OpenAI-compatible with tool calling |
| Ideation | DONE | `brainstorming` skill; three alternatives generated and folded in or cut |
| Idea approval | DONE | LLM council: 5 advisors, 5 anonymised peer reviews, chairman. **Approved with major reshaping** |
| Spec | DONE | `docs/SPEC.md` in `to-spec` format. No git repo and no issue tracker, so the file is the tracked spec |
| Implementation plan | DONE, APPROVED | `docs/superpowers/plans/2026-09-10-say-less.md`, 20 tasks, TDD, full code inline, 89-test suite. Six review rounds, each reconstructing every module and executing the suite. Final round: 87/87 green against a 290-name surname list, every earlier defect reproduced on demand to prove the fix, nothing blocking |
| **Gate measurement** | **DONE — Go, confidence-independent** | Plan Task 1. Full result below in "The gate" |
| Repair engine (plan Tasks 2–9) | IN PROGRESS | Sep 11–15 |
| Stream, keyterms, harness (Tasks 10–14) | BLOCKED | Sep 16–18 |
| Session, server, front end (Tasks 15–17) | BLOCKED | Sep 19–22 |
| Deploy (Task 18) | BLOCKED | Sep 23 |
| Video, deck, cover image (Task 19) | BLOCKED | Sep 24–27 |
| Submit | BLOCKED | Sep 28 |

## What the council changed

The idea survived. The design did not survive intact. Five changes, all binding:

1. **The trigger moved off confidence and onto set membership.** Confidence cannot detect a confidently-wrong word, which is the failure that matters most. Membership of the field's allowed-value set can, and does so independently of the recogniser.
2. **The candidate comes from the field, not the recogniser.** AssemblyAI exposes no N-best, so "Tuesday?" is produced by phonetic matching against the field's value set. The council called this the most important consequence of the verified API facts.
3. **Tool-call blocking is cut** to a single commit-time readback. Five competing submissions already occupy the refuse-unverified-actions lane; the unoccupied claim is recovery.
4. **Duplex and barge-in are cut.** Repair fires at end of turn, after fields bind, so the mechanism never needs to interrupt.
5. **The second-language demo clip is cut.** Double metaphone is English-specific and would exercise the weakest component.

Rejected outright: shipping a pip-installable package. Four of five reviewers named that the council's biggest blind spot for a solo builder with this timeline.

## The gate

**Do this before writing or building anything else.** One Python file, tonight.

Stream ~15 pre-recorded difficult utterances — files, not a live microphone — through Universal-Streaming. Each fills a bounded field whose true value and full value set are known: seven weekdays, 120+ surnames, ten service names. Log per-word confidence and the final flag; for the field's value, log its double-metaphone ranking against that field's value set.

Record three clips per item, not one: the full sentence twice, so the baseline gets a genuine second attempt rather than a replayed one, and the field value alone, so a category question's word count is measured rather than assumed. Plus one shared "yes" and one shared "no". The slot's word range is recorded in the manifest and the value is extracted by position, so the measurement does not grade itself.

Three numbers:
- What fraction of misheard field tokens fall outside the value set entirely.
- Of the misheard ones that fall inside it, whether their confidence sits below that of correctly-heard tokens.
- How often the true value ranks first or second phonetically within the set.

**Decision rule, fixed now, before the numbers exist:**

| Result | Decision |
|---|---|
| True value ranks first or second in ~60%+ of wrong-token cases | **Go.** The offer mechanism works as specified |
| Candidate recovery is good but confidence does not separate right from wrong | **Go, confidence-independent.** Trigger on set membership alone, drop confidence from the pitch |
| Wrong tokens are usually valid in-set members held with high confidence | **Kill.** No trigger exists. Fall back to publishing the harness as a repair-quality benchmark, reusing this same script |

The script and its recordings become the evaluation harness and the test fixtures. The gate and the first deliverable are the same artifact — which is the council's stated countermeasure against this repo becoming another thorough spec that never ships.

### Gate result (2026-09-10)

**Note on corpus drift:** the transcript below was captured before the 2026-09-11 corpus fix that removed incidental time-of-day mentions from `day_02` and `day_05` (see the decision log below). Re-running `gate/measure.py` today would show slightly different text for those two items; the gate's rank-recovery finding and Go decision are unaffected, since both items were still heard and recovered correctly either way.

**Run against a real microphone recording could not happen** — the build was executed by an AI agent with no ability to speak into a microphone. The 15 utterances (5 each for `day`, `service`, `surname`) were instead synthesized with Windows SAPI (`Microsoft David Desktop` for takes 1 and answers, `Microsoft Zira Desktop` for take 2, so the two takes are genuinely different voices) at 16 kHz/16-bit/mono, then deliberately degraded: a 16 kHz→8 kHz→16 kHz narrowband round-trip (simulates a phone codec discarding everything above ~4 kHz) plus additive white noise at a randomised 6–14 dB SNR for full sentences and 14–20 dB for short answers. Scripts: `scripts/build_synth_jobs.py`, `scripts/synthesize.ps1`, `scripts/degrade_audio.py`. **This is a real, documented limitation, not a hidden one** — see the README's "Audio corpus" section. Synthetic degraded TTS is not the same distribution as real accented, noisy, phone-quality human speech, and the result below should be read as "the mechanism is not obviously broken," not as "validated against real callers."

Actual output of `python gate/measure.py`:

```
day_01     truth=Tuesday          heard=tuesday, please    wrong=True  conf=1.00 in_set=False rank=1
day_02     truth=Monday           heard=monday             wrong=False conf=1.00 in_set=True  rank=1
day_03     truth=Wednesday        heard=wednesday          wrong=False conf=1.00 in_set=True  rank=1
day_04     truth=Thursday         heard=thursday           wrong=False conf=1.00 in_set=True  rank=1
day_05     truth=Friday           heard=friday             wrong=False conf=1.00 in_set=True  rank=1
svc_01     truth=beard trim       heard=beard trim         wrong=False conf=0.96 in_set=True  rank=1
svc_02     truth=haircut          heard=haircut            wrong=False conf=1.00 in_set=True  rank=1
svc_03     truth=hot towel shave  heard=hot towel shave, please wrong=True  conf=0.99 in_set=False rank=1
svc_04     truth=head massage     heard=head massage       wrong=False conf=1.00 in_set=True  rank=1
svc_05     truth=kids cut         heard=kid's cut          wrong=True  conf=0.98 in_set=False rank=1
sur_01     truth=Sharma           heard=sharma             wrong=False conf=0.99 in_set=True  rank=1
sur_02     truth=Patel            heard=patel              wrong=False conf=0.98 in_set=True  rank=1
sur_03     truth=Nguyen           heard=nguyen             wrong=False conf=0.98 in_set=True  rank=1
sur_04     truth=Hardeep          heard=hardeep            wrong=False conf=0.73 in_set=True  rank=1
sur_05     truth=Rodriguez        heard=rodriguez          wrong=False conf=0.96 in_set=True  rank=1

scored: 15 (alignment failures: 0)
misheard slot values: 3
  fell outside the value set:  3/3 (100%)
  truth at phonetic rank 1-2:  3/3 (100%)   <-- GO threshold is 60%
mean confidence, correct:      0.967
mean confidence, misheard:     0.992
  confidence separates:        False
```

**Reading it honestly.** All three "misheard" rows are not genuine phonetic substitutions — the synthetic degradation, layered on already-crisp TTS pronunciation, wasn't harsh enough to make AssemblyAI mishear a word. Two are the position-aligned slot extractor picking up a trailing word from an adjacent insert region (`"tuesday, please"`, `"hot towel shave, please"`); one is an orthographic normalisation difference (`"kid's cut"` vs `"kids cut"`). All three still landed outside the exact-match value set, and all three were still recovered at phonetic rank 1 — which is a real property of the matcher even though it wasn't stress-tested by a genuine mishearing in this run.

**Decision, applying the pre-committed rule exactly as written, without reinterpreting it:**

- Rank recovery: 3/3 = 100%, clears the 60% bar for plain **Go**.
- Confidence separation: **failed** — misheard-token confidence (0.992) was *higher* than correct-token confidence (0.967), the opposite of what a confidence-based trigger would need.

Both rows of the decision table are technically satisfied, but confidence provides zero (in this sample, negative) discriminating power, so the honest call is the second row: **Go, confidence-independent.** n=3 misheard cases is a small sample and this finding is not statistically strong on its own, but the sample-size caveat cuts against trusting confidence more, not less, so confidence-independent is the conservative reading either way.

**Correction found during implementation (Task 8).** The first attempt implemented "confidence-independent" literally: `CONFIDENCE_THRESHOLD = 0.0` in `src/sayless/schema.py`, shared by both arms per the plan's Task 3 note. Writing and running `tests/test_baseline.py` immediately surfaced the problem: the baseline planner has *no* set-membership concept — confidence is its only trigger — so zeroing the shared threshold silently disabled the baseline entirely (two tests crashed with the baseline never firing at all, `AttributeError: 'NoneType' object has no attribute 'kind'`). An inert baseline would have rigged the A/B comparison in Say Less's favour for a reason that has nothing to do with the actual design difference, which is precisely the kind of comparison-integrity bug the six plan-review rounds were built to catch — it just hadn't been caught yet because the plan review executed the *plan's* tests, not this project's actual gate-driven configuration.

Fix: `CONFIDENCE_THRESHOLD` is restored to `0.65` (a literature-typical confidence floor), shared by both arms so neither is arbitrarily handicapped. "Confidence-independent" is represented correctly in `planner.py`'s control flow instead — an out-of-set value always triggers a repair regardless of confidence, by construction, independent of whatever this constant is set to. That is what actually makes Say Less's headline claim (it catches a confidently wrong value the baseline can't) true, and it was true before and after this fix. The constant only governs two secondary things: Say Less's in-set-but-shaky fallback, and the baseline's entire trigger — and the gate's finding is honestly represented by *not* claiming that secondary Say Less mechanism as validated, rather than by breaking the baseline.

## Key facts to not forget

- Five equal winners at $1,000 cash + $1,000 credits each. Not ranked; no single first place.
- Judging is equally weighted across Application of Technology, Presentation, Business Value, Originality. Three of the four are pitch, not engine.
- Submission needs all of: public GitHub repo, hosted demo URL, video presentation, slide deck, cover image, title, short and long descriptions, tech tags.
- Judges include AssemblyAI's founder/CEO and Head of Realtime. The technology claim will be read by the people who built the model.
- Submissions must be original and MIT-compliant. SLURP audio is CC BY-NC 4.0, so it must be downloaded by script, never committed.
- API credits require signing up through the hackathon's own link, with cookies accepted during sign-up. If an account already exists, log out first and re-enter through that link.
- Registration stays open all month; only the submission deadline is fixed.
- Using a company email at registration is encouraged but optional.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Confidence does not discriminate misheard words | Trigger is set membership, not confidence. The gate's middle outcome is explicitly survivable |
| A confidently wrong candidate is offered live to a judge | Offers fire only for out-of-set values or in-set-but-low-confidence ones. One offer per field, two repairs per turn, then degrade |
| Repair loop during the demo | Hard caps, then open request, then escalate. Non-negotiable |
| Audio plumbing consumes the schedule | Browser microphone and browser speech synthesis only. No vendor TTS, no native Windows audio, no barge-in |
| The differentiator gets built last and cut | Build order inverted: engine over saved JSON on days 2–6, front end not until day 10 |
| Benchmark dismissed as self-serving | Baseline is the same pipeline with only the planner swapped, on identical waveforms; primary corpus is external (SLURP) |
| Crowded "verify the agent" lane | Message stays on recovery, never refusal. Readback never appears in the title or first slide |
| Deadline slip | Target Sep 28, two days of slack against a hard 8:30 PM IST cutoff |
| Spec written, nothing shipped | The gate script is both the go/no-go and the first deliverable |

## Open questions

- Whether SLURP's entity annotations map cleanly onto bounded value sets, or whether the self-recorded slice has to carry the evaluation alone. Given the schedule, Task 14 is expected to be skipped per its own stated default.
- ~~Whether the reactive keyterm push measurably improves retry success.~~ Measured (2026-09-11): identical results with the flag on and off on this corpus. Not because the push is ineffective — because no item in this 15-item corpus required a second audio stream (a real retry after a rejection), so the reactive push's effect was never exercised. It is implemented, unit-tested (`tests/test_keyterms.py`), and used identically by both the harness and the live demo session; measuring its effect on retry accuracy needs a corpus item where an offer is genuinely rejected, which this one doesn't have.
- Where to host: Render or Fly. Both fine; decide on Sep 23, not before.
- Whether "Say Less" survives contact with the deck. Reversible until the cover image is made.

## Decision log

- **2026-09-10** — Hackathon page fetched and summarised; competitor field surveyed and grouped by theme.
- **2026-09-10** — Literature scanned; gap located between the conversation-analysis account of repair and the engineering account of voice-agent failure. Nobody has built agent-side repair-format selection.
- **2026-09-10** — API feasibility verified. The absence of N-best is the finding that reshaped the design.
- **2026-09-10** — Capacity set at solo/evenings; stack set at Python backend plus minimal web front end.
- **2026-09-10** — Council convened. Verdict: build it, reshaped around the slot rather than the confidence score, gated on one evening of measurement. Contrarian's mechanism attack judged strongest by three of five reviewers; Expansionist's scope expansion judged the biggest blind spot by four of five.
- **2026-09-10** — Renamed Locus → Say Less on the Outsider's objection that the old name communicated nothing.
- **2026-09-10** — Plan approved after six review rounds. The defects that mattered most were invisible to reading and only showed up when a reviewer ran the code: an off-by-one in the gate's reference data that would have read as Kill and killed the project on a typo; a rejection branch that bypassed every cap and offered 122 consecutive surnames; a measurement harness running a different policy than the demo, which made the seam score worse than the baseline on the one branch it exists to improve; and a surname guard that passed against the 20-name starter list and failed against a real one.
- **2026-09-10** — Implementation plan written, reviewed and corrected. The review executed the plan's own test files and found the phonetic threshold set above the value the real confusion produces, so `STRONG` is now 0.65 rather than 0.72, measured rather than guessed. Three integrity fixes followed from the same review: the gate now extracts the slot by position rather than by similarity to the answer it is grading, every word count in the evaluation is read off a real recording including a value-only answer clip per item, and the baseline reads its confidence threshold from the same schema as the seam so the two arms cannot drift apart.
- **2026-09-10** — Gate run for real against AssemblyAI. No human speaker was available, so audio was synthesized with Windows SAPI TTS and deliberately degraded (narrowband round-trip + noise) as a documented substitute — see "Gate result" above and the README's limitations. Result: 15/15 scored, 3 misheard, all 3 recoverable at phonetic rank 1 (100%, clears the 60% bar), but confidence did not separate correct from wrong (misheard confidence was *higher* on average). Decision: **Go, confidence-independent.** Implementation of Tasks 2–19 begins.
- **2026-09-10** — Task 8's tests caught a comparison-integrity bug in Task 3's literal implementation of "confidence-independent": `CONFIDENCE_THRESHOLD = 0.0` shared by both arms silently disabled the baseline's only trigger (it has no set-membership fallback), which would have made the A/B comparison a strawman. Corrected to a shared `0.65`; the confidence-independence the gate found is represented in `planner.py`'s unconditional out-of-set trigger instead. See "Correction found during implementation" above.
- **2026-09-11** — Tasks 2–18 implemented and committed following the plan exactly, all 89 tests passing at each step. Public repo created and pushed: https://github.com/HarshdipSaha/say-less
- **2026-09-11** — First real run of `evalharness.run` surfaced a serious bug the plan's six review rounds could not have caught, because it only shows up against the LLM Gateway's actual behaviour: the field binder's prompt (bare field names, "day, time, service, surname", no description) returned an empty binding for every single real gate day-sentence. The harness's first run measured nothing but repeated escalations. Fixed in two steps: (1) added a one-line description per field, which fixed most sentences but two remained empty, and separately a naive one-shot clean example ("Friday") fixed those two but caused a *worse* regression — it reclassified a genuinely misheard value ("chewsday") from the day field to the service field instead of preserving it, breaking the core mechanism this project depends on; (2) a second, deliberately different example (a garbled value staying in its correct field) fixed all five real day-sentences without that regression. Verified through the real `bind()` function, not just isolated prompt experiments. Binder caches poisoned by the two broken prompt versions were cleared before the harness was re-run. See `src/sayless/binder.py` and the README's "Known issues found and fixed during the build".
- **2026-09-11** — The same paired clean/garbled-example fix was needed a second time for the `service` field (independently discovered: "I would like a beard trim" and "just a haircut today thanks" both returned empty bindings under description-only). Applied identically, re-verified the day/chewsday regression check still holds with both fields' examples present in one prompt.
- **2026-09-11** — A clean harness run then surfaced a corpus-design bug, not a mechanism bug: two `day` items ("...on Monday morning", "Friday afternoon...") incidentally mentioned a time of day. Since `time`'s allowed values are specific hour slots, "morning"/"afternoon" are out-of-set, and Say Less correctly (but irrelevantly to the day/service/surname comparison) triggered a repair on the `time` field for those two items, adding noise to the words-re-said and turns-to-resolution averages. Fixed by removing the incidental time mentions, re-synthesizing and re-degrading just the four affected audio clips, purging the stale cache entries for them, and re-running.
- **2026-09-11** — **Final measured result** (`eval_results.json`, reactive keyterms on): Words re-said 0.00 (baseline) vs 0.07 (Say Less); Turns to resolution 1.00 vs 1.00; **Commit accuracy 93% vs 100%**; Escalation 0% vs 0%; Residual 0% vs 0%. On 14/15 items both arms committed identically. On the 15th (`svc_05`), the recogniser produced a possessive near-miss ("kid's cut" for "kids cut") that the baseline committed silently and wrongly, while Say Less caught the set-membership mismatch, offered the correct value, and got a one-word confirmation — at zero extra turns. This is a small, favourable, synthetic-audio corpus (see README limitations): it demonstrates the mechanism firing correctly on a real (if narrow) case, not a production accuracy claim. The repair ladder's costlier branches (two-way offer, category question, rejected-offer turn cost) are implemented and unit-tested but were not exercised by this run, since no item produced a genuine phonetic mishearing severe enough to trigger them.
- **2026-09-11** — Both keyterm conditions run per Task 13 Step 6 (`eval_results.json` vs `eval_results_nokeyterms.json`): identical tables. Honest reading above, not "no effect" — this corpus never exercises a retry.
- **2026-09-11** — Reproducibility verified per spec story 22 (Task 13 Step 8): cloned the pushed repo into a clean directory, created a fresh venv, `pip install -e ".[dev]"`, ran the full suite (89/89 passed), then ran `ASSEMBLYAI_API_KEY= python -m evalharness.run --offline` — reproduced the exact same table with **0 cache misses**, no network call, no API key. The committed `corpus/transcript_cache.json` and `corpus/binder_cache.json` are genuinely sufficient on their own.
