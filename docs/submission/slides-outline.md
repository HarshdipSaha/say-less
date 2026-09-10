# Slide deck outline (5 slides)

Build these in Google Slides / PowerPoint / Keynote — this file is the content outline, not the deck itself, since I can't produce a binary slide file directly.

## Slide 1 — The problem
**Headline:** "Sorry, could you repeat that?" is the least informative question a voice agent can ask.

- One line: when a voice agent mishears you, it re-asks the whole sentence, not the one word it missed.
- Human conversation repairs misunderstanding constantly (~once per 1.4 min, every language studied) by asking the *most specific* question the evidence supports — never the generic one.
- The gap: nobody in this space asks about the word. (Cite: council research scan, `docs/research-3w-scan.md`.)

## Slide 2 — The mechanism
**Headline:** Set membership, then the specificity ladder.

- Diagram: turn transcript → LLM binds fields → is the value in the field's known set? → NO → phonetic match against the set → pick the most specific move.
- Ladder (with example utterances): restricted offer ("Tuesday?") → two-way offer ("Tuesday or Thursday?") → category question ("Which day?") → open re-ask.
- One sentence: the candidate comes from the *field's own value list*, never from the recogniser — AssemblyAI returns no alternative hypotheses.

## Slide 3 — Why this needs Universal-Streaming
**Headline:** The managed Voice Agent API can't see what we need.

- Side-by-side: Voice Agent API `transcript.user` payload (plain text only) vs. Universal-Streaming `Turn` payload (`words[]` with `confidence`, `word_is_final`, plus `end_of_turn_confidence`).
- The keyterms loop: push the field's value set before the caller speaks; push the narrowed candidates again after a repair.
- LLM Gateway for field binding (OpenAI-SDK compatible, one call).

## Slide 4 — Results
**Headline:** 93% → 100% commit accuracy, at a cost of 0.07 words per booking.

- Table (baseline vs. Say Less, reactive keyterms on): words re-said 0.00 vs 0.07 · turns to resolution 1.00 vs 1.00 · **commit accuracy 93% vs 100%** · escalation 0% vs 0% · residual 0% vs 0%.
- The one item that differed: the recogniser transcribed a possessive apostrophe onto "kids cut" → "kid's cut", a near-miss just outside the field's exact value set. Baseline committed it silently and wrongly. Say Less caught the mismatch, offered "kids cut?", got a one-word "yes" — zero extra turns.
- Business value: at this accuracy delta, ~667 wrong bookings avoided per 10,000 calls; at a typical $7–12 loaded human-recovery-call cost (Retell AI, 2026), that's $4,667–$8,000 per 10,000 calls in avoided recovery cost alone.
- Residual (0%): stated honestly as the failure bucket this design cannot see by construction — every error either arm made was in this corpus's reach, which is a property of this small corpus, not a general guarantee.
- Caveat, said out loud, not buried: this is a small, synthetic (TTS + degraded), favourable corpus. Read the numbers as "the mechanism fires correctly," not as a production accuracy claim — see README "Audio corpus" and "Results".

## Slide 5 — What it doesn't solve, what a month adds
**Headline:** Scoped honestly.

- Doesn't solve: confidently-wrong in-set values; ordinary-English-word surnames need one extra turn; no barge-in.
- A month would add: real recorded audio across accents, SLURP as an external corpus, tuned per-field thresholds, a packaged repair-planner library.
- Close on the mechanism, not the metric: "the agent asks about the word, not the sentence."
