# Submission text (lablab.ai)

## Title
Say Less

## Short description (one line)
A voice agent that asks about the one word it missed, instead of asking you to repeat the whole sentence.

## Long description

When a voice agent mishears you, it says the same thing every time: "Sorry, I didn't catch that, could you repeat that?" That question is the least informative one available — it forces you to re-say the entire sentence to fix one word, and the same hard word gets misheard again under the same conditions.

Human conversation doesn't work this way. Across every language studied, people resolve misunderstanding roughly once every 1.4 minutes, and they always ask the most specific question their evidence supports — naming a candidate ("Tuesday?") beats asking a category ("which day?") beats asking blind ("sorry, what?").

Say Less brings that behaviour to a voice agent, for the specific case where a field has a known, bounded set of allowed values — a day of the week, a service from a menu, a surname from a customer list. AssemblyAI's Universal-Streaming API exposes per-word confidence and finality that the managed Voice Agent API does not; Say Less uses that evidence to detect when a value doesn't belong in its field's set, and phonetically matches the heard value against that set to produce a specific, named repair question instead of a generic one. The loop closes by pushing the narrowed candidate set back into the recogniser as keyterms before the retry.

Built on: AssemblyAI Universal-Streaming (Realtime Speech-to-Text), AssemblyAI LLM Gateway, FastAPI, browser Web Audio + Web Speech API. No barge-in, no vendor TTS — push-to-talk only, by design, to keep the mechanism legible.

**An important limitation, stated up front:** the gate measurement and demo corpus were built by an AI agent with no ability to record a human voice, so the 15-utterance test corpus is synthesized (Windows SAPI text-to-speech, two voices) and then deliberately degraded (narrowband phone-codec simulation + noise) rather than recorded from a real caller. See the README's "Audio corpus" section for exactly what that does and does not establish.

## Technology tags
AssemblyAI, Universal-Streaming, Realtime Speech-to-Text, LLM Gateway, Voice Agent, FastAPI, Python

## Category tags
Voice AI, Conversational AI, Speech Recognition, Customer Service

## Links
- Public repository: https://github.com/HarshdipSaha/say-less
- Live demo: _fill in after Render deploy — see docs/STATUS.md "Open questions"_
- Video: _fill in after recording_ (see `docs/submission/video-script.md`)
