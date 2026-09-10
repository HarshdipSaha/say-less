# WHY / HOW / WHAT scan — conversational repair in voice AI agents

Mode: `deep-research` → `three-way-scan` (ARS). Compact shortlist, then cross-paper synthesis.
Date: 2026-09-10. Purpose: locate an unresolved gap a 3-week hackathon project can actually fill.

---

## Shortlist

### P1 — Dingemanse, Roberts, Baranova, Blythe, Drew, Floyd, Gisladottir, Kendrick, Levinson, Manrique, Rossi & Enfield (2015). *Universal Principles in the Repair of Communication Problems.* PLOS ONE 10(9): e0136100.

**WHY.** Conversation constantly breaks down, and no account existed of whether the machinery humans use to fix it is culture-specific or universal. If it is universal, it is infrastructure, not etiquette.

**HOW.** Systematic comparison of naturally occurring conversation in 12 languages from 8 unrelated families, coding every instance of other-initiated repair (OIR): one party signals trouble, the other fixes it.

**WHAT.**
- OIR is universal and *frequent*: on average once per **1.4 minutes**, in every language sampled.
- Three initiator formats recur everywhere, ordered by how much they specify:
  1. **Open request** — "Huh?", "What?" — signals only that something failed.
  2. **Restricted request** — "Who?", "When?" — locates the trouble to a category.
  3. **Restricted offer** — "Bob?", "You mean Tuesday?" — names a *candidate* and asks for confirmation.
- The governing principle: speakers **prefer the most specific format they can produce**, because specificity minimises cost for the person who must repair and for the dyad jointly.
- Repair is cheap when done right: the two-utterance repair sequence is on average no longer than the single utterance being fixed.

---

### P2 — *An Analysis of Dialogue Repair in Voice Assistants* (arXiv:2311.03952, 2023).

**WHY.** Voice assistants misunderstand constantly; the paper asks whether they participate in repair the way humans do.

**HOW.** Empirical interaction study against Google Assistant and Siri, probing their handling of the open-class initiator "huh?", plus acceptability surveys with English and Spanish speakers.

**WHAT.** Assistants have some repair-ish strategies but **cannot replicate human repair**, notably the open-class initiator. Users' preferences differ by language. The paper frames this as an inequality between human–human and human–machine interactional language.

---

### P3 — *"Mm, Wat?" Detecting Other-initiated Repair Requests in Dialogue* (arXiv:2510.24628, 2025).

**WHY.** Agents fail to notice when the *user* initiates repair, which turns a recoverable misunderstanding into a breakdown.

**HOW.** Multimodal classifier over Dutch dialogue, fusing linguistic features with prosodic features, both grounded in Conversation Analysis, on top of pretrained text and audio embeddings.

**WHAT.** Prosody complements text and significantly improves detection. The contribution is **recognition of user-initiated repair**, direction user → agent.

---

### P4 — *SpeechGym: An Audio-Native Gym for Training Voice Agents via RL* (arXiv:2608.26432, 2026).

**WHY.** Voice agents are trained and measured in text, so nobody knows what speech itself costs them.

**HOW.** Audio-native environment: two omni-modal models converse in raw audio over the unmodified tasks, tools and success checks of an established text agentic benchmark, making modality the only variable. Trained with per-turn process rewards.

**WHAT.** The decisive finding for product design:
> "The failures speech introduces are **perceptual rather than reasoning deficits**: the agent picks the right tool and the right argument slot but **fills it with a value misheard from the waveform**, and that single error cascades into a failed call, a retry of the same call, and a wasted step budget."

Second failure mode: under an insistent caller the agent performs an **unauthorised write and ends the episode believing it helped**. Both are cheap to label because the database itself adjudicates them.

---

### P5 — *Better Retrieval, Worse Robustness: How Multi-hop RAG Amplifies Upstream ASR Errors* (arXiv:2608.22872, 2026).

**WHY.** Spoken queries pass through ASR before any retrieval, so ASR error is a fixed upstream constraint; do smarter downstream pipelines absorb it or amplify it?

**HOW.** Four RAG configurations across three multi-hop QA benchmarks, four synthesised English accents, measured against a clean-text oracle.

**WHAT.** Richer structure **amplifies** the error: the clean-to-worst-accent F1 gap is **36–67% larger** under entity-graph linking plus iterative reformulation than under naive dense retrieval. The dominant failure is **corruption of query entities, 87–96% of degradation cases**. Two lightweight surface-form fixes leave most of the gap intact.

**Supporting non-academic evidence.** Hamming AI's production study across 10M+ minutes and 10K+ voice agents names "noise-driven omissions" as failure mode #1, defined by the fact that content is dropped *without indication of loss*, and confirms that a fresh ASR model can improve aggregate accuracy while starting to mishear account numbers.

---

## Cross-paper synthesis

### Common WHY
All five start from one premise: **the transcript is not the message.** Something is lost between the waveform and the agent's representation of what was said, and the loss is invisible at the point where it matters. P1 says humans evolved a universal, high-frequency mechanism to handle exactly this. P2–P5 say machines have not.

### Divergent HOW
The papers split cleanly along two axes, and the split is where the gap lives.

| | Studies the *human* mechanism | Studies the *machine* failure |
|---|---|---|
| **Detects / diagnoses** | P1 (typology + preference principle), P3 (agent detects user's repair) | P4 (localises failure to argument slots), P5 (localises failure to entities) |
| **Repairs** | P2 (finds assistants *cannot*) | — **empty** — |

P1 and P3 look at repair as a *social* object. P4 and P5 look at the same breakdown as an *engineering* defect and never mention repair. P2 is the only paper that stands in both worlds, and its result is negative.

### Strongest WHAT
P4's sentence is the strongest single finding in the set, because it converts a vague quality complaint into a precise, addressable defect: the agent's **reasoning is correct and its perception is wrong**, the damage enters through **one argument value**, and the agent proceeds anyway. P5 independently corroborates the same shape from a different direction, quantifying it at 87–96% of degradation, and adds the uncomfortable result that making the downstream pipeline smarter makes this worse rather than better. P1 supplies the missing half: the fix is not better transcription, it is a **repair move chosen at the right level of specificity**.

### The unresolved gap

Put the two halves next to each other and the hole is obvious.

- P1 establishes that competent speakers **localise the trouble source** and then choose the **most specific repair initiator** their evidence supports, and that this is universal, routine and cheap.
- P4 and P5 establish that a voice agent's trouble source is almost always **localised already** — it is one entity, one argument value, one slot.
- P2 establishes that deployed assistants nonetheless emit only the **least specific** repair move available ("Sorry, I didn't catch that, could you repeat?"), or none at all.

So deployed voice agents possess the information needed to run the human repair system and throw it away. They hold per-word confidence, they know which slot they are filling, and they respond to trouble with an undifferentiated open-class request that forces the user to re-say an entire utterance — violating both of P1's principles at once: not the most specific format, and a repair sequence far longer than the trouble source.

**Nobody has built the agent-side repair selector.** P3 built detection in the user → agent direction. The agent → user direction, where the agent initiates repair on its *own* perceptual trouble and picks the format by evidence, is unoccupied.

**What would fill it.** A component that (a) localises the trouble source at word level from streaming ASR evidence rather than at utterance level, (b) maps that evidence to P1's three initiator formats under the most-specific-possible rule, and (c) refuses to let an action execute on an argument whose evidence never cleared threshold. That last clause is what separates it from a politeness feature and attaches it to P4's unauthorised-write failure.

**What makes it buildable now, on this stack.** AssemblyAI Universal-Streaming returns per-word `confidence`, a per-word `word_is_final` flag that exposes which words are still being revised, and `end_of_turn_confidence`. That is precisely the localisation evidence P1's preference rule needs and P2's assistants never had. Note the managed Voice Agent API does **not** expose it: its `transcript.user` payload carries plain `text` only. The evidence exists on exactly one of the two hackathon paths.

### Caveats on this scan
Five papers is a scan, not a review. P1 is a 2015 linguistics result being applied outside its evidentiary scope; it describes human speakers, and nothing in it guarantees users will accept the same moves from a machine — P2's survey data in fact hints that acceptability varies by language. P4's finding comes from omni-modal self-play, not production telephony. The Hamming figures are vendor-published and not peer reviewed.
