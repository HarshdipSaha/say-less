# Council Verdict — approved with major reshaping

Convened 2026-09-10 on the question: build "Locus" for the AssemblyAI Voice Agent Hackathon, or pick a different idea?
Full transcript: `docs/council/transcript.md`. Outcome: **build it, reshaped around the slot rather than the confidence score, gated on one evening of measurement.**

Note on naming: the council reviewed the project as "Locus." The Outsider's objection to that name ("told me nothing; I read it as a location product") was accepted after the verdict, and the project is now called **Say Less**. Everything below is the chairman's verdict as delivered.

---

## Where the Council Agrees

**Build Locus.** Four of five advisors say build it; the fifth (Outsider) doesn't say don't — it says the pitch hides its own mechanism and never names a buyer. Nobody proposed switching ideas, and no reviewer proposed one either. That convergence is real but it is weaker than it looks, because it was unanimous agreement on the *idea* while three separate reviewers independently flagged that nobody had verified the *mechanism*. Treat "build Locus" as agreed and "build Locus as currently specified" as not agreed.

**The build plan, not the idea, is the thing that kills this.** Executor, Contrarian and First Principles converge hard: hand-building the duplex stack (mic capture, streaming socket, turn detection, external TTS, barge-in) on Windows consumes all 19 evenings, and none of it is the differentiator. The differentiator would be the last thing built and the first thing cut. Given a documented history of specs that never ship, this is the single highest-probability failure mode — higher than the mechanism being wrong.

**Cut the tool-call blocking as a headline feature.** Contrarian, First Principles and Expansionist agree independently. Five submitted competitors already occupy the refuse-unverified-actions lane. Locus's unoccupied claim is *recovery* — re-asking one word — and refusal dilutes the one sentence a judge remembers.

**The eval harness is the highest-leverage single artifact.** First Principles and Executor both land here from different directions: it is simultaneously the test suite, the deck's data slide, the Business Value number, and the thing that cannot be faked at 11pm on the 29th. Most entrants will have a demo and no numbers.

**Judges score a video, a deck and roughly 90 seconds of hosted demo — not the repo.** Three of four equally weighted criteria are pitch. This is First Principles' core reframe and Reviewers 4 and 5 both named it the strongest single contribution in the council.

## Where the Council Clashes

**Validation gate versus artifact-first.** Executor and Contrarian want Evening 1 spent proving the API fact before anything else exists. First Principles wants the build order derived backwards from the one persuasive clip. These read as opposed but are not: the resolution is that Evening 1's output *is* the first piece of the deliverable. Stream pre-recorded files, not a live mic, and the validation script becomes the fixed clip set, which becomes the eval harness, which becomes the data slide. The gate and the artifact are the same file. Anyone who tells you to choose between them has mis-set the granularity.

**Scope: contain versus expand.** Expansionist stands alone — pip-installable middleware, a format taxonomy delivering three features "for free", benchmark-as-product, a second-language clip. Four of five reviewers named this the council's biggest blind spot, and they are right about the build implications: it is scope creep dressed as leverage, proposed for a solo dev with 19 evenings and a track record of unshipped specs, on a premise nobody had tested. But Expansionist has one asset the others discard too fast: *the metric is genuinely unowned*. "Words the user was forced to re-say" and turns-to-resolution are not instrumented anywhere in this space. Take the positioning, refuse the build. Naming and owning a metric costs one slide. Shipping a package costs a week you do not have.

**Is the mechanism even sound?** Contrarian is the only advisor who attacks the causal claim rather than the plan, and three of five reviewers called it the strongest response for exactly that. The attack: low confidence is not the same as wrong word, and the canonical failure — dates, names, account numbers lost without indication of loss — is precisely the case that returns *high* confidence on a wrong token. "Tuesday" heard as "Thursday" is confidently wrong. If the localiser mis-points, Locus offers a confidently wrong restricted candidate, which is strictly worse than "please repeat," in front of the two people on earth most likely to spot it.

This clash is now half-settled by the verified facts, and settled in a direction nobody anticipated. See below.

**Whether Outsider's critique counts.** Reviewer 2 dismissed it as line-editing on a pitch document. That dismissal is wrong. Outsider asked "who is this for?" and "where does Thursday come from?" — one of those is 25% of the judging rubric (Business Value) and the other is the exact gap that Reviewers 2, 3 and 4 then independently escalated into the council's central technical hole. Outsider found the hole first and was penalised for phrasing it as a clarity problem instead of an engineering one.

## Blind Spots the Council Caught

**The candidate-generation mechanism was never specified, by anyone.** Outsider noticed it; Reviewers 2, 3 and 4 escalated it. Every advisor assumed "the ASR hands you a ranked alternative." Reviewer 4 correctly identified this as a cheaper and more fundamental Evening-1 test than the confidence test Executor proposed. All ten participants also assumed that if there is no N-best, the whole mechanism collapses. It does not collapse — it relocates. That is the most important thing the verified facts change.

**Nobody discussed a degraded Evening-1 result.** Reviewer 1's catch. Executor framed it as binary: fields discriminate or Locus is dead. A partial signal is the likeliest outcome and needs a decision rule in advance, before you are motivated to read the numbers charitably.

**Nobody checked whether the cut features are secretly load-bearing.** Reviewer 2's catch, and the sharpest process observation in the whole review round: injecting a clarification mid-turn *is* an interruption pattern, so cutting barge-in may cut the core mechanic. Resolved below, and the resolution is favourable.

**Nobody named a concrete alternative idea.** Reviewer 1. The question was "Locus or something else" and the council answered a different, easier question. Addressed below.

**Nobody found Keyterms Prompting.** This is a blind spot of all ten participants, not just one, and it is the single strongest AssemblyAI-native move available in this project. Details below.

## The Recommendation

**Build Locus. Reshape it around the slot, not the confidence score. Gate it on one evening of measurement tonight.**

### What the verified facts do to the design

The absence of N-best is not a wound, it is the design. Since the ASR cannot propose "Thursday," the candidate must come from the *expected value set of the slot being filled* — the seven weekdays, this customer's twelve surnames, this catalogue's product names — matched phonetically (double metaphone). That single relocation changes four things at once:

1. **It defines the product honestly.** Locus is a repair layer for **bounded slots**: dates, names from a known list, SKUs, account numbers. Not general conversational repair. This is a smaller claim and a truer one, it removes roughly fifteen evenings of work, and it happens to describe most of contact-center voice AI. Say it in the first line of the deck. It also answers Outsider: the buyer is the developer or contact-center operator shipping the voice agent, and their number is containment rate, not caller happiness. The caller-side "you hang up" framing must go.

2. **It gives you a trigger that does not depend on confidence at all.** If the token that landed in the slot is not a member of the slot's value set, that alone fires a repair. Confidence becomes a second, independent signal rather than the load-bearing one. This is what makes Locus survive a degraded Evening-1 result.

3. **It makes the Dingemanse specificity ladder the actual policy rather than decoration.** Outsider called the twelve-languages research decoration, and as written it was. Implemented, it is the fallback chain: strong phonetic rank-1 match to one slot member gives a restricted offer ("Tuesday?"); two close members give a two-way offer ("Tuesday or Thursday?"); no plausible member gives a category repair ("which day?"); and only then an open repair. That ladder is your originality story, it is defensible under questioning, and it degrades gracefully on camera instead of failing.

4. **It kills one piece of Expansionist's advice outright.** Double metaphone is English-phonology-specific. The "record one clip in a second language" multiplier is now actively bad — it would demo the weakest part of your stack. Cut it.

### Keyterms Prompting is the move nobody saw

Universal-Streaming accepts up to 100 keyterms per session and accepts `UpdateConfiguration` mid-session. Use it twice:

- **Prospectively.** Push the slot's value set as keyterms *before* the turn — this caller's three upcoming appointment dates, their surname, the twelve products they own. This shrinks the high-confidence-but-wrong bucket at the source, which is a direct structural answer to Contrarian's killer objection rather than a mitigation of it.
- **Reactively.** After a repair fires, push the narrowed candidate set as keyterms so the retry is biased toward exactly the words in play, then measure retry success rate with and without the push.

That closed loop — detect, offer, re-bias the recogniser, retry — is a roadmap argument for the Head of Realtime delivered as a working demo, and it is the "teaches AssemblyAI something about its own product" asset Expansionist was reaching for, at a cost of one message type instead of a week of packaging.

### The repair policy on high-confidence-but-wrong tokens

Do not repair them. You cannot detect them, and pretending otherwise is how you produce the confidently-wrong offer that loses the demo. The policy is three-tier:

- **In-set, high confidence:** accept silently. No repair. Prospective keyterms have already reduced this bucket.
- **Out-of-set, or in-set with low confidence:** repair, using the specificity ladder above. **Hard cap: one restricted offer per slot, at most two repairs per turn, then degrade to open repair.** A repair loop in front of judges is the worst available outcome and this cap is non-negotiable.
- **Consequential slots at commit time:** one single readback of the whole booking before the action fires ("Tuesday the 14th at 3 — correct?"). This is the only surviving descendant of tool-call blocking, it costs one line of code, and it is framed as recovery, not refusal — you fix the value and then act, rather than declining to act. One sentence in the deck, never a feature slide.

And measure the residue. Report the high-confidence-wrong number honestly on a slide as the bucket Locus does not solve. Judges who built the ASR will respect an owned failure mode far more than a suspiciously clean chart, and it pre-empts the exact question the founder will ask.

### Duplex and barge-in: cut, and Reviewer 2's objection does not bite

Push-to-talk only. Web Audio to your socket, Web Speech API for TTS, no vendor TTS, no Windows audio stack, no barge-in. Reviewer 2 worried that mid-turn clarification is itself an interruption and might secretly require the cut features. It does not, because **repair fires at end of turn, before the tool call, not mid-utterance** — you need the slot bound to know the candidate set, and slot binding happens after the turn completes. Universal-Streaming gives you turn boundaries natively via `end_of_turn_confidence`, so even turn detection is not hand-built. The cut is clean.

### Tool-call blocking, formally

Cut as a feature. Kept as one line of commit-time readback. Never mentioned in the title, the cover image, or the first slide.

### On switching ideas

Do not. The three alternatives you set aside are not alternatives any more — the benchmark is now the eval harness inside Locus, phonetic readback is now the candidate matcher plus the commit-time readback, and the interruption ledger is cut with barge-in. There is no live competing idea, and switching on Sept 10 with a spec-writing habit is strictly worse than reshaping. The one honest exception is in the kill condition below.

### Schedule

Sept 10 (tonight): the measurement, below. Sept 11–15: repair engine as pure Python over saved transcript JSON, no audio — localise, phonetic match, ladder, keyterms push. Sept 16–18: eval on 20 fixed clips, baseline versus Locus, turns-to-resolution and words-re-said, run on the identical waveform through both pipelines. Sept 19–22: browser front end, push-to-talk, one fake tool (`book_appointment`), slot vocabulary visible on screen — which fences the failure mode *and* makes the mechanism legible. Sept 23: deploy to Render or Fly. Sept 24–27: video, deck, cover image, with the split-screen clip and the dollars-per-10k-calls slide built from your own measured deltas times a cited public per-minute cost. **Submit Sept 28.**

## The One Thing to Do First

Tonight, before writing a single line of design document: write one Python file that streams roughly fifteen pre-recorded noisy utterances — not a live mic — through Universal-Streaming, where each utterance fills a bounded slot whose true value you know and whose full value set you have (seven weekdays, twenty surnames, ten product names). Log per-word `confidence` and `word_is_final`, and for the slot token log its double-metaphone ranking against that slot's value set. Then compute three numbers: what fraction of misheard slot tokens fall outside the value set entirely; of those that fall inside it, whether their confidence sits below the confidence of correctly-heard tokens; and how often the true value is phonetic rank 1 or 2 within the set.

Decide in advance, tonight, before you see them:

- **Go** if the true value is rank 1 or 2 in roughly 60% or more of wrong-token cases. The offer mechanism works.
- **Go, confidence-independent** if candidate recovery is good but confidence does not separate wrong from right. Trigger on set-membership alone and drop confidence from the pitch — this is the degraded case the council never planned for, and it is survivable.
- **Kill** only if wrong tokens are usually *valid in-set members* with high confidence. Then there is no trigger, Locus cannot fire, and on Sept 11 you still have eighteen evenings and a working harness — at which point the benchmark idea, which needs no live repair mechanism, becomes the fallback using the file you wrote tonight.

Those files are your eval set. That script is your harness. This is the gate and the first deliverable in one evening, and it is the only thing standing between this council verdict and another thorough spec that never ships.
