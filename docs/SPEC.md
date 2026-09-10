# Spec: Say Less — repair for bounded slots in voice agents

A voice agent that asks about the word it missed, not the sentence.

Project for the **AssemblyAI Voice Agent Hackathon** (lablab.ai × AssemblyAI), Sep 1–30 2026, on the Realtime Speech-to-Text path.
Written in the `to-spec` format. This directory is not a git repository and no issue tracker is configured, so **this file is the tracked spec**; the triage label would be `ready-for-agent`.

Status: `docs/STATUS.md` · Council verdict: `docs/council/verdict.md` · Research: `docs/research-3w-scan.md` · Hackathon brief: `docs/hackathon-brief.md`

> **Gate.** This spec is conditional. It is not approved for implementation until the Evening-1 measurement in `docs/STATUS.md` returns Go or Go-confidence-independent. If it returns Kill, the fallback named in Out of Scope applies. Do not build past Task 1 before the gate resolves.

---

## Problem Statement

I ship voice agents. My agents fail in one specific way far more often than any other, and I currently have no tool that addresses it.

The agent understands the caller perfectly well. It picks the right action and the right field. Then it writes into that field a value it misheard from the audio, and it proceeds as though nothing happened. The caller said Tuesday; the booking says Thursday. The caller said their surname; the record says a different surname. Nothing in my stack knows this has occurred, because the transcript is the only thing my language model ever sees, and the transcript looks like a perfectly ordinary sentence.

When my agent does notice trouble, its only response is the same undifferentiated sentence every time: *"Sorry, I didn't catch that, could you repeat that?"* That question is the least informative one available. It tells the caller nothing about what went wrong, so the caller re-says the entire utterance, so the same acoustically difficult word arrives again under the same conditions, and it is misheard again. Two or three rounds of that and the caller either abandons the call or demands a human. Both outcomes are the thing I bought a voice agent to avoid, and both show up in the only number my business cares about, which is what fraction of calls the agent finishes on its own.

I know from my own logs that the damage concentrates in a handful of fields: dates, names, product identifiers, account numbers. I also know these fields have something in common that my agent does not exploit: **I already know what values are allowed in them.** There are seven weekdays. This caller has four appointments. My catalogue has 300 products. My agent has that list sitting in a database and never once consults it when deciding whether it heard the caller correctly.

## Solution

Say Less is a repair layer that sits between streaming speech recognition and the agent's action, for the specific case where the field being filled has a **known set of allowed values**.

It does two things no deployed voice agent does today.

**It decides whether it misheard by asking the field, not the recogniser.** When a value lands in a bounded field, Say Less checks whether that value is a member of the field's value set. A non-member is direct evidence of a mishearing, and that evidence is independent of how confident the recogniser was. Per-word confidence is used as a *second, weaker* signal for values that are in-set, never as the primary trigger. This ordering is deliberate and it is the design's load-bearing decision: the failure that hurts most is a confidently wrong word, and confidence by construction cannot detect it, whereas set membership can.

**It asks the most specific question its evidence supports.** Instead of one generic re-ask, Say Less selects among four repair moves, ordered by how much they narrow the problem for the caller. Where the mishearing sounds like exactly one allowed value, it names that value and asks for a yes: *"Tuesday?"* Where two are close, it offers both: *"Tuesday or Thursday?"* Where nothing plausible is close but the field is known, it asks the category: *"Which day?"* Only when it cannot even locate the trouble does it fall back to the generic re-ask that today's agents start with. This ladder is not a stylistic choice. It is the empirically universal structure of human conversational repair, and its governing rule — always use the most specific form your evidence supports, because that minimises cost for the person who has to fix it — is exactly the rule current voice agents violate.

Because the candidate values are known at the moment of the re-ask, Say Less also pushes them into the recogniser as keyterms before listening again, so the retry is biased toward the handful of words actually in play. Detect, offer, re-bias, retry — the loop closes.

The claim is deliberately narrow. Say Less is **not** general conversational repair and **not** an improvement to speech recognition. It is a behaviour layer for bounded fields. That covers most of what contact-centre voice agents actually do, and it is a claim that can be defended under questioning rather than one that collapses on the second demo attempt.

The result is measured, not asserted: the same audio waveform is replayed through a baseline agent and through Say Less, and the comparison reports how many words the caller was forced to re-say, how many turns it took to reach the correct value, and how often the committed value was right.

## User Stories

1. As a developer shipping a voice agent, I want the agent to detect that a value it wrote into a bounded field is not a permitted value for that field, so that a mishearing is caught before it becomes a wrong booking.
2. As a developer, I want that detection to work even when the recogniser reported high confidence, so that the confidently-wrong failure mode is covered rather than assumed away.
3. As a developer, I want per-word confidence used as a secondary signal for values that are in-set, so that a plausible-but-shaky value still gets checked.
4. As a developer, I want to declare a field's allowed values as ordinary data alongside the field's name and type, so that adding a new bounded field costs me a list and not a code change.
5. As a developer, I want to mark a field as consequential, so that the value gets read back once before an irreversible action regardless of how confident the system is.
6. As a developer, I want the repair behaviour to be a pure function of the turn's evidence and the field schema, so that I can unit-test every repair decision without audio, a microphone or a network call.
7. As a developer, I want a hard cap on repairs per field and per turn, so that a caller can never be trapped in a clarification loop.
8. As a developer, I want the agent to escalate to a human after the cap is exhausted, so that failure is bounded and visible instead of endless.
9. As a developer, I want the system to push a field's allowed values to the recogniser as keyterms before the caller speaks, so that the mishearing is less likely to happen in the first place.
10. As a developer, I want the narrowed candidate set pushed as keyterms immediately after a repair is asked, so that the caller's correction is recognised against the two or three words actually in play.
11. As a developer, I want to measure retry success with and without that keyterm push, so that I know whether the re-biasing earns its complexity.
12. As a contact-centre operator, I want to know how many words my callers are forced to repeat, so that I have a number for a failure that currently shows up only as abandonment.
13. As a contact-centre operator, I want to know how many turns it takes to reach a correct value, so that I can connect repair quality to average handle time.
14. As a contact-centre operator, I want the fraction of calls that commit a correct value, so that I can connect repair quality to containment rate.
15. As a contact-centre operator, I want those three numbers computed by replaying the same recordings through my current agent and through Say Less, so that the comparison is not confounded by different callers or different audio.
16. As a caller, I want to be asked about the one word that was missed rather than told to repeat myself, so that fixing the problem costs me a single word.
17. As a caller, I want to be offered a candidate I can confirm with "yes", so that I do not have to re-articulate a word that was already hard to recognise.
18. As a caller with an accent the recogniser handles poorly, I want the system to narrow to a small set of options rather than repeatedly failing on open recognition, so that I am not disproportionately forced to escalate.
19. As a caller, I want the agent to read back a consequential value once before acting, so that an error is caught before it costs me an appointment.
20. As a caller, I want a wrong candidate to be correctable in one turn, so that a bad guess by the agent does not cost more than the generic re-ask would have.
21. As a hackathon judge, I want to see the same recording produce a generic re-ask in one pane and a specific question in the other, so that the difference is legible in a few seconds without narration.
22. As a hackathon judge, I want the numbers on screen to be reproducible from the public repository with one command, so that I can believe them.
23. As a hackathon judge assessing use of the technology, I want to see which specific AssemblyAI streaming fields are consumed and why the managed Voice Agent API could not supply them, so that I can tell whether the integration is deep or decorative.
24. As a hackathon judge, I want the failure mode the system does *not* solve reported as a number, so that I can trust the numbers it does report.
25. As a researcher or engineer reading the repository, I want the mapping from repair-initiation types in the conversation-analysis literature to the implemented moves stated explicitly, so that I can check that the ladder is implemented rather than merely cited.
26. As a maintainer, I want the evaluation corpus downloaded by a script rather than committed, so that the repository's own licence stays clean.
27. As a maintainer, I want each repair decision logged with the evidence that produced it, so that I can inspect why a particular question was asked.
28. As a maintainer, I want the recogniser client, the field binder, the candidate matcher and the repair planner to be separable, so that I can replace the phonetic matcher without touching anything else.
29. As the builder, I want the Evening-1 measurement script to become the evaluation harness, so that the go/no-go gate and the first deliverable are the same artifact.
30. As the builder, I want a written decision rule for a partial result, fixed before I see the numbers, so that I cannot rationalise a weak signal into a green light.

## Implementation Decisions

**Path.** The Realtime Speech-to-Text path, not the managed Voice Agent API. This is forced, not preferred: the Voice Agent API's user-transcript events carry plain text only, with no words array and no confidence, so the evidence this project runs on does not exist on that path. The language model is AssemblyAI's LLM Gateway, which is OpenAI-SDK-compatible and supports tool calling. Speech output is the browser's own speech synthesis. No third-party text-to-speech vendor and no local Windows audio stack.

**Six modules, one repository, Python.**

- **Stream client.** Holds the Universal-Streaming websocket. Per turn it accumulates an evidence record: for each word, the text, the confidence, the final flag and how many times that position changed across partial results; plus the turn's transcript and its end-of-turn confidence. Revision churn is recorded because it is free to collect, and it is reported separately from confidence rather than blended into it.
- **Field binder.** After end of turn, a single LLM Gateway tool call extracts field values from the turn transcript and returns, for each value, the character span it occupied. Spans are mapped back to word indices so that each bound field carries the evidence for exactly the words it came from. Asking the model for spans rather than just values is what makes the evidence attributable.
- **Candidate matcher.** Double metaphone over the field's declared value set. Returns set membership for the heard value and a ranked list of candidates with scores. Pure, synchronous, no network.
- **Repair planner.** The one decision point. Takes the turn's evidence, the bound fields and the field schema; returns a repair move or nothing. Pure function, no I/O.
- **Keyterms controller.** Pushes a field's value set before the turn in which that field is expected, and the narrowed candidate set immediately after a repair, using the mid-session configuration update. Capped at 100 terms, each 50 characters or fewer, per the API limit. Whether the reactive push is enabled is a flag, because story 11 requires measuring both.
- **Evaluation harness.** Replays fixed audio files through the baseline pipeline and the Say Less pipeline and emits the metrics table.

**The field schema is data.** A field declares a name, a type, its allowed values (inline, or a reference the host application resolves), whether it is consequential, and its confidence threshold. Adding a bounded field is adding a list.

**The repair ladder.** This is the spec's core policy. Evidence about the value bound to a field maps to exactly one move:

| Evidence | Move | Shape of the utterance |
|---|---|---|
| In set, confidence at or above threshold | Accept, silently | — |
| In set, confidence below threshold | Restricted offer | "Tuesday?" |
| Not in set, exactly one candidate above the phonetic threshold | Restricted offer | "Tuesday?" |
| Not in set, two candidates close together | Two-way offer | "Tuesday or Thursday?" |
| Not in set, three or more candidates, or none plausible | Restricted request | "Which day?" |
| Field not bound at all, or end-of-turn confidence low | Open request | "Sorry, say that again?" |

The four moves correspond to the repair-initiation types documented as universal across languages: restricted offer, restricted request and open request, with the two-way offer a bounded variant of the restricted offer. The ordering encodes the same preference rule those studies found — take the most specific form the evidence supports.

**Caps, and they are not negotiable.** At most one restricted offer per field. At most two repair moves per turn. On exhaustion, degrade to an open request, then escalate to a human. A clarification loop in a live demo is a worse outcome than any mishearing.

**Consequential fields bypass the ladder at commit time.** Before an irreversible action, the assembled values are read back once as a single confirmation. This is the only surviving element of the action-gating idea the council cut, it is one call, and it is framed as recovery rather than refusal: the value gets corrected and the action then proceeds. It is not a headline feature and does not appear in the project title or the first slide.

**Confidence is explicitly demoted.** High-confidence, in-set, wrong values are out of reach of this design and are not chased. They are counted and reported as the residual. Prospective keyterms are the only measure taken against them, and they act before the error rather than after.

**The baseline is the same pipeline with the planner swapped.** Identical stream client, identical binder, identical language model. The baseline planner emits an open request whenever any word falls below threshold or a field fails to bind, which is current deployed behaviour. Identical waveforms go through both. No other difference exists, so no other difference can explain the result.

**Demo scenario: appointment booking.** One tool, `book_appointment`. Fields: day of week (seven values), time slot (a fixed list), service type (a short list), customer surname (a fixture list of roughly 200). Chosen because every field is naturally bounded, the domain needs no explanation to a judge, and surname is a genuinely hard recognition target. The front end is push-to-talk, browser microphone to the websocket, with the field schema and the live evidence visible on screen so the mechanism is legible rather than magical.

**No barge-in, no full duplex, no hand-built turn detection.** Repair is decided at end of turn, after fields are bound, which is strictly after the caller has stopped speaking. The core mechanic therefore never needs to interrupt, and the streaming API supplies turn boundaries natively. This is why cutting duplex does not cut the mechanism.

## Testing Decisions

**What makes a good test here.** A test asserts on the repair move that was chosen and on the numbers the harness reports. It never asserts on how the planner reached the move, on prompt text, or on the internals of the matcher. Swapping double metaphone for another phonetic algorithm must not break a single planner test.

**The repair planner is the seam.** It is a pure function from evidence plus schema to a repair move, and it is where essentially all behaviour lives. Every row of the ladder table, every cap, and every degradation path is a table-driven case against hand-written evidence fixtures. No audio, no network, no API key. This is the highest available seam and the design deliberately concentrates behaviour behind it so that one seam suffices.

**The candidate matcher gets its own narrow tests,** because it is the component most likely to be replaced: known confusable pairs rank each other highly, an exact member ranks first, and an input unlike anything in the set produces no candidate above threshold.

**The stream client is tested against recorded fixtures,** not a live socket. Saved websocket frames from the Evening-1 run replay into the client and the resulting evidence record is asserted. This keeps the whole suite offline and deterministic and means the gate measurement pays for the test fixtures.

**The harness is the integration test.** Running it on the dev slice must reproduce the reported metrics exactly, from a clean checkout, with one command. Story 22 makes reproducibility a requirement rather than a nicety.

**Metrics, defined precisely because they are the deliverable.** Words Re-Said counts the words the caller utters in turns that exist only because a repair was asked. Turns to Resolution counts turns from first mention of a field to a correct bound value. Commit Accuracy is the fraction of runs whose committed values all match ground truth. Residual is the fraction of wrong values that were in-set and above threshold, the bucket this design cannot see.

**Corpus.** Dev slice: roughly 15 self-recorded utterances covering each field, deliberately difficult, with known ground truth and known value sets. Primary evaluation set: 20–40 utterances from SLURP's far-field recordings, which carry entity annotations and come from 177 native and non-native speakers, with the matching headset recordings of the same utterances available as an easy-condition control. SLURP audio is CC BY-NC 4.0, so it is fetched by a download script and never committed, keeping the repository's own licence clean and MIT-compatible as the hackathon rules require. If SLURP integration costs more than one evening, the fallback is the self-recorded slice alone with that limitation stated on the slide rather than hidden.

**Prior art for these tests.** None in this repository; it is empty. The table-driven planner tests are the pattern to establish first, and everything else follows their shape.

## Out of Scope

- General open-domain conversational repair. Say Less only handles fields with a known value set. Free-text fields fall through to the open request, which is current behaviour.
- Detecting high-confidence, in-set, wrong values. Counted and reported, never chased.
- Barge-in, full duplex, and interruption recovery.
- Non-English phonetics. Double metaphone encodes English phonology, so a second-language demo would exercise the weakest component and is explicitly cut.
- Any third-party text-to-speech vendor, and any native Windows audio work.
- Publishing a packaged library. The repair engine stays inside this repository for the hackathon. The positioning claim about owning the metric is made on a slide, not by shipping a package.
- Blocking or refusing tool calls as a feature. Reduced to a single commit-time readback.
- Telephony. Browser microphone only; no phone number, no carrier integration.
- Multiple scenarios or multiple tools. One tool, `book_appointment`.
- Speaker diarization, emotion, and multi-party audio.
- Fine-tuning or training anything.

**Fallback if the gate returns Kill.** If wrong values turn out to be usually in-set and confidently held, there is no trigger and this design cannot fire. The fallback is then the measurement harness itself, published as a repair-quality benchmark for voice agents, which needs no working repair mechanism and reuses the Evening-1 artifact directly. That decision belongs to Sep 11, not to a later week.

## Further Notes

**Why this is not the same as the neighbouring submissions.** Several entries in this hackathon verify, gate or evidence an agent's actions — refusing to act until an argument is traced or approved. Say Less is about **recovery**, not refusal: the question the agent asks when it knows something went wrong. The unoccupied claim is that nobody re-asks a single word, and the messaging must stay on that claim.

**Why the technology story is defensible.** The whole design consumes fields that exist on exactly one of the hackathon's two paths. Per-word confidence, the per-word final flag and end-of-turn confidence come from Universal-Streaming; the managed Voice Agent API's transcript events carry only text. Keyterms Prompting, with its mid-session configuration update, closes the loop by re-biasing the recogniser toward the candidates in play. That is a deep integration argument rather than a decorative one, and it is addressed to judges who include the people who built the streaming model.

**On honesty in the numbers.** The residual metric exists because a chart with no failures invites the question of what was hidden. Reporting the bucket this design cannot address is expected to be worth more with these particular judges than a cleaner result would be.

**Naming.** The project was reviewed by the council as "Locus". That name was changed to "Say Less" after an advisor reported reading it as a location product. "Say Less" names the metric — the caller says fewer words — and reads as the idiom meaning the listener has understood. This is a reversible decision and costs nothing to revisit before the deck is built.

**Provenance of the framing.** The repair typology and the most-specific-form-possible preference rule come from a cross-linguistic study of twelve languages. The characterisation of the failure as perceptual rather than reasoning — right tool, right field, misheard value — comes from a 2026 audio-native agent study. The concentration of downstream damage in corrupted entities comes from a 2026 study of spoken retrieval. Sources and the gap analysis are in `docs/research-3w-scan.md`.
