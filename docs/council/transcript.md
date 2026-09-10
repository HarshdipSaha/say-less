# LLM Council — transcript

Question: build "Locus" for the AssemblyAI Voice Agent Hackathon, or pick a different idea?
Convened 2026-09-10. Method: Karpathy-style LLM Council (5 independent advisors → anonymised peer review → chairman synthesis).
Verdict: `docs/council/verdict.md`. Research inputs: `docs/research-3w-scan.md`, `docs/hackathon-brief.md`.

---

## The framed question

Solo developer, evenings and weekends only, ~19 days to a hard deadline of Sep 30 2026 8:30 PM IST. Python backend plus minimal web front end, Windows machine. Documented track record of writing thorough specs that then never get implemented.

Hackathon: lablab.ai + AssemblyAI, $10,000 across five equal winners, judged equally on Application of Technology, Presentation, Business Value and Originality. Requires a public repo, a hosted demo URL, a video, a slide deck and a cover image. ~2,660 registrants and 35–40 projects already submitted, several occupying "block unverified actions / transcript evidence" territory. Judges include AssemblyAI's founder and Head of Realtime.

**Locus**, as pitched to the council: a voice agent that asks about the one word it actually missed ("Tuesday?") instead of asking the user to repeat the whole sentence. Grounded in Dingemanse et al. 2015 (repair once per 1.4 minutes, universal preference for the most specific repair format), SpeechGym 2026 (voice agent failures are perceptual, not reasoning — right tool, right slot, misheard value), and the fact that AssemblyAI's Universal-Streaming exposes per-word confidence while its managed Voice Agent API does not.

Alternatives set aside: a pure repair-quality benchmark; an interruption-recovery ledger; a phonetic-readback module.

---

## Round 1 — the five advisors

### The Contrarian

The fatal flaw isn't the idea. It's that you've chosen the hard path on purpose, and your track record is specs that never ship. Rejecting the managed Voice Agent API means you hand-build the duplex stack: streaming STT socket, turn detection, LLM gateway, external TTS, barge-in, plus a hosted demo where a judge's laptop mic works over the public internet. That's the whole 19 evenings before the repair engine exists. Your differentiator is the last thing you'd build and the first thing you'd cut.

Second: interrogate the mechanism, not the citations. Low confidence does not mean wrong word. The failure Hamming describes — names, dates, account numbers lost "without indication of loss" — is precisely the case that returns high confidence on a wrong token. "Tuesday" heard as "Thursday" is confidently wrong. `word_is_final` flags revision, not error. If your localiser mis-points, Locus produces confidently wrong restricted offers — "You mean Thursday?" — which is strictly worse than "please repeat," and a judge will hit that on the second try in the live demo. Have you actually pulled per-word confidence on ten noisy utterances and checked whether the low-confidence word is the wrong word? If not, the entire premise is unvalidated and that test costs one evening. Do it tonight.

Third: blocking unconfirmed tool-call arguments is already submitted twice by competitors; it buys negative originality. Cut it.

Fourth: three of four equally-weighted criteria are pitch, not engine, and a self-run benchmark against a strawman baseline you wrote yourself will not survive a skeptical judge.

Keep Locus. Kill the ambition. Scripted vertical, fixed slot types, demo-first, mechanism validated by Friday — or you ship another spec.

### The First Principles Thinker

You're asking which idea to build. The actual question is what artifact the judges score, and it isn't a repo.

Judges score a video, a deck, and maybe 90 seconds of a hosted demo. Nothing in the criteria rewards a working repair engine — three of four criteria reward a *legible difference*, and the fourth rewards one specific thing you already identified: that word-level confidence and `word_is_final` exist in Universal-Streaming and nowhere in the managed Voice Agent API. That single fact is your entire technology score. Everything else you build is set dressing for it.

So rebuild the scope from that. The irreducible unit of persuasion is a split-screen: same noisy utterance, baseline says "sorry, could you repeat that?", Locus says "Tuesday or Thursday?", with a counter showing words the user was forced to re-say. That is the deliverable. The repair engine exists to make that clip true. Build the eval harness and the fixed noisy-utterance set *first* — it is simultaneously your test suite, your deck's data slide, and your proof against a track record of specs that die unimplemented, because a harness with numbers in it cannot be faked at 11pm on the 29th.

Second reframe: cut the tool-call blocking. That is Voice Action Gate's and the claim-intake agent's ground, it's *refusal*, and it makes you a third entrant in a crowded lane. Locus's genuinely unoccupied claim is **recovery** — nobody in that field re-asks one word. Blocking dilutes the one sentence a judge will remember.

Locus is right. The nineteen evenings are the wrong unit — you have one clip and four slides. Build backwards from those.

### The Expansionist

Build Locus, and stop thinking of it as a hackathon app. You're sitting on the only entry that teaches AssemblyAI something about its own product.

The undervalued asset isn't the agent — it's the metric. "Words the user was forced to re-say" and turns-to-resolution don't exist as instrumented numbers anywhere in this space. Own them. Ship the repair engine as a pip-installable middleware with the benchmark harness in the same repo. Then every competitor becomes a downstream consumer rather than a rival. They built products; you built the layer underneath them. That reframing is worth more than the demo.

The two ideas you set aside aren't alternatives, they're features that fall out for free. Barge-in recovery is a repair format ("you were saying, the amount?"). Phonetic readback is the restricted-offer format applied to a name slot. Implement the format taxonomy properly and you get all three, which makes your originality story a framework rather than a trick.

Biggest asymmetry: AssemblyAI's Head of Realtime and founder are judging, and your project's central claim is that their managed Voice Agent API throws away the exact signal that fixes their customers' top failure mode. That's a roadmap argument delivered as a working demo. Nobody else in a field of 2,660 is going to hand them that. Winning is almost the smaller outcome — the credits, the DevRel relationship, the cookbook post, being the reference implementation people cite.

Two multipliers, cheap: record one clip in a second language, and put the A/B number on slide one in dollars per 10k calls.

### The Outsider

(Given only the pitch, with no context about the builder, the field or the research.)

**What I didn't understand.** "Voice agent" versus "voice assistant" — you use both, and I assumed they were the same thing until "you hang up," which suddenly told me this is a phone call, not a smart speaker. That flip happens mid-paragraph and I had to reread. Also: where does "Thursday" come from? You said the system knows it's unsure about a word. You never said how it produces a plausible alternative to offer. That is the part I'd want explained, and it's the one part that's missing. I assumed the STT engine hands you a ranked list; if it doesn't, you've hidden the hard problem.

**What I assumed wrongly.** I first read this as an improvement to speech recognition itself. It isn't — it's a behavior layer on top. Say that early. "Locus" told me nothing; I read it as a location product.

**Who is it for?** I genuinely can't tell. The story is written from the caller's side ("you hang up"), but nobody buys software for the person who hangs up. Is the customer a contact-center operator? A developer buying an SDK? Unstated.

**Doing no work.** The twelve-languages research. It's decoration — I already accepted "humans ask about the word" from your example.

**So what?** The last paragraph. You describe your measurement setup in detail and then give me zero results. That reads like you're hiding a weak number. Put the actual figure in the sentence — "3.2 back-and-forths down to 1.4" — or cut the paragraph.

### The Executor

Verdict: build Locus, but only after Evening 1 proves the one API fact everything rests on. Then cut the duplex loop entirely.

The idea is fine. The build plan is the problem: hand-building microphone capture, streaming socket, turn detection, TTS playback and barge-in is 60 hours by itself, on Windows, and none of it is the thing being judged.

- **Evening 1 (tonight, 3 hours, no spec):** one Python file, one websocket to Universal-Streaming, speak five noisy sentences, print `confidence` and `word_is_final` per word to console. Nothing else. If those fields don't discriminate misheard words from correct ones, Locus is dead and you've lost one evening, not fourteen. Do not write a line of design doc before this runs.
- **Days 2–6:** repair engine as pure Python over saved transcript JSON. No audio. This is the entire original contribution and it's testable with fixtures.
- **Days 7–9:** the eval. 20 fixed noisy clips, baseline vs Locus. This *is* your Presentation and Business Value score. Most entrants will have a demo and no numbers.
- **Days 10–13:** browser front end. Web Audio mic to your socket, Web Speech API for TTS. No TTS vendor, no Windows audio stack, no barge-in, push-to-talk only. One fake tool.
- **Day 14:** deploy. Not day 18.
- **Days 15–17:** video, slides, cover image. Submit Sep 28, not Sep 30.

Cuts: barge-in, full duplex, end-of-turn tuning, multiple tools, any second scenario.

Where it dies: you spend evenings 1–4 writing a spec instead of opening a socket, then discover audio plumbing on Windows in week three.

---

## Round 2 — anonymised peer review

Advisors were shuffled to letters before review: **A** = Executor, **B** = Contrarian, **C** = Outsider, **D** = Expansionist, **E** = First Principles. Reviewers did not know the mapping.

**Tally — strongest response:** B ×3, E ×2.
**Tally — biggest blind spot:** D ×4, C ×1.

### Reviewer 1
Strongest: **B** — the only response that attacks the causal mechanism instead of the pitch. "Low confidence ≠ wrong word, and the failure mode described is exactly the case that returns high confidence on a wrong token" is a falsifiable risk none of the others raise as sharply. E is close but assumes B's premise is true.
Blind spot: **D** — recommends scope expansion for a solo dev with 19 evenings and a track record of specs that never ship, and never runs the evening-1 validation at all; it leaps to platform ambition on an unverified premise.
All missed: the question was "build Locus or pick a different idea," and nobody named a concrete alternative to compare against. Nobody discusses a *degraded* evening-1 result — partial signal, rather than binary dead-or-go.

### Reviewer 2
Strongest: **B** — attacks the load-bearing assumption everyone else takes for granted, shows Locus could produce a failure mode worse than the baseline it replaces, live, in front of the judges who built the tool, and proposes a one-evening test to settle it.
Blind spot: **C** — never answers the actual question; reads as line-edit feedback and treats "where does Thursday come from" as a clarity problem rather than the central unvalidated mechanism.
All missed: nobody specifies the alternative-generation mechanism as an engineering deliverable — how "Thursday" gets proposed, and what happens with multiple low-confidence words or no plausible alternative. Also: A cuts duplex and barge-in, but *injecting a mid-turn clarification is itself an interruption pattern* — nobody checks that the cut features aren't secretly required by the core mechanic.

### Reviewer 3
Strongest: **B** — the only one attacking the load-bearing technical claim rather than the plan around it.
Blind spot: **D** — expands scope inside a 19-evening solo sprint and never proposes a single cut, only additions dressed as things that "fall out for free."
All missed: how Locus generates the candidate it offers. This needs either an N-best list from Universal-Streaming or a hand-built phonetic-confusion model — a second load-bearing API fact as critical as confidence, and nobody proposes testing it on Evening 1.

### Reviewer 4
Strongest: **E** — correctly identifies the actual scoring object (video, deck, 90-second demo, not the repo) and derives build order from that, making the sharpest falsifiable cut without needing D's speculative upside.
Blind spot: **D** — treats "AssemblyAI's founder is judging" as leverage rather than as a risk that a broken live demo is judged by the people who would know immediately if the mechanism claim is wrong.
All missed: nobody asks whether Universal-Streaming actually returns N-best hypotheses. If there is no ranked alternative, the confidently-wrong failure mode and the whole repair-question mechanism collapse together — a cheaper and more fundamental evening-1 test than the confidence-discrimination one.

### Reviewer 5
Strongest: **E** — the only one tying build order directly to the judging rubric, and it makes the eval harness do triple duty as test suite, deck data and anti-procrastination device.
Blind spot: **D** — leaps to platform ambition with 19 evenings and one person, never addresses the build risk.
All missed: nobody except B engages the confidence-miscalibration challenge as something to *test* before deciding build order. The council should merge A's validation-gate structure with B's specific falsification test.

---

## Facts established between rounds

Verified against AssemblyAI's documentation after the advisors responded, and supplied to the chairman:

1. **Universal-Streaming exposes no N-best or alternative hypotheses.** Per word it gives `confidence`, `word_is_final` and timings, plus a turn-level `end_of_turn_confidence`. The candidate offered in a repair cannot come from the recogniser.
2. **The managed Voice Agent API carries plain `text` only** in its user-transcript events — no words array, no confidence. The differentiating signal exists on exactly one of the two hackathon paths.
3. **Keyterms Prompting** accepts up to 100 terms per session, each 50 characters or fewer, biases the model toward them, and can be updated mid-session via an update-configuration message.
4. **The LLM Gateway** is OpenAI-SDK-compatible across 25+ models with tool calling and streaming.

Fact 1 is the one that changes the design: it converts the Outsider's comprehension complaint into a required component.
