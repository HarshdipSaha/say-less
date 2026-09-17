# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Hackathon judges/reviewers evaluating the "Say Less" AssemblyAI Voice Agent Hackathon submission. They arrive at the live demo page, hold a push-to-talk button, speak a real booking sentence into their own microphone, and judge the submission by what happens in that one turn.

## Product Purpose

A live, interactive demo of a voice-agent repair mechanism. When a caller's turn ends, the agent checks whether the transcribed value for a bounded field (day / service / surname) is a member of that field's known allowed set. If it isn't, the agent asks the smallest possible repair question — name one candidate, offer two, ask the category — instead of asking the caller to repeat the whole sentence. Success is a judge holding the button, saying a sentence, seeing (and hearing, via TTS) a targeted repair question appear, and understanding in under a minute why that beats "sorry, could you repeat that?" — without reading much text to get there.

## Positioning

The repair trigger is set membership, not a confidence score — a confidently-wrong word that isn't a valid field value still gets caught. The candidate the agent offers back is never invented by the speech recognizer; it's the closest phonetic match against the field's own allowed values. This is what separates it from a generic "low confidence → re-ask" voice agent.

## Operating Context

Single-page browser demo. A push-to-talk button ("hold to talk") captures real microphone audio and streams it over a WebSocket to a FastAPI backend, which proxies to AssemblyAI Universal-Streaming for transcription and AssemblyAI's LLM Gateway for the binding/repair decision. The agent's spoken reply plays back through the browser's SpeechSynthesis API. No login or accounts. One booking flow runs at a time, across three fields: day, service, surname. Results render live as the conversation happens, not after the fact.

## Capabilities and Constraints

Real, functioning audio pipeline — not a mockup: `getUserMedia` mic capture, Float32→PCM16 downsampling to 16kHz client-side, raw PCM streamed to `/ws`. The server pushes four message types the UI must keep surfacing:

- `schema` — the allowed values for each bounded field, sent once at connect.
- `turn` — the live transcript for the caller's turn, per word, each with a confidence score and a revision count.
- `agent` — the agent's reply text, the current booking values (partial or complete), which repair "move" it made (accept / name-one / offer-two / ask-category / re-ask), and a `done` flag.
- Spoken playback of the agent's reply via TTS.

This is a redesign of presentation and interaction, not the mechanism: every one of the above must still be shown somewhere, just organized so the primary flow doesn't read as a debug console. Runs via `uvicorn app.server:app`; static frontend has no build step (plain HTML/CSS/JS, no framework) and that stays as-is.

## Brand Commitments

Name "Say Less" and the tagline "The agent asks about the word, not the sentence." are established across the README, pitch deck, and teaser image — both are binding. A marketing teaser image exists at `docs/submission/teaser.png` using a dark blue/cyan palette; that's marketing collateral, not an app DESIGN.md, so it's a visual hypothesis to weigh during the visual-world decision, not a locked constraint.

## Evidence on Hand

Real measured benchmark: 93% → 100% commit accuracy, 0.07 words re-said per booking, evaluated against real recorded calls plus the public SLURP corpus and a phone-degraded test set (see `README.md`, `docs/STATUS.md`). These are real numbers, not placeholders — safe to reference, never round up or embellish. No customer logos, testimonials, or case studies exist; don't fabricate any.

## Product Principles

1. The mechanism must be legible in one live turn — a judge holding the button once should see the repair happen, not read documentation to understand it.
2. Never hide or dumb down the real signal (per-word confidence, the allowed-value schema, the exact booking JSON, the repair move) — surface it, but don't let it compete with the primary flow for attention.
3. The conversational exchange — what was heard, what the agent asked, what got booked — is the headline. The transparency panels are supporting evidence, reachable but secondary.
4. This is a live system talking to a real API over a real microphone, not a canned script — the UI must honestly reflect connecting / listening / thinking / speaking states, including failure (no mic permission, connection drop).

## Accessibility & Inclusion

Agent replies are already announced via an `aria-live` region; keep that. Push-to-talk is currently mouse/touch-only (`mousedown`/`touchstart`) with no keyboard path — worth a keyboard-accessible equivalent (e.g. spacebar hold) since this will be operated live by judges who may not all use a mouse.
