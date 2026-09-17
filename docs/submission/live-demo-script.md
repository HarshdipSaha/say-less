# Live demo recording script

Exact words to say into the push-to-talk key, verified against the real pipeline (real AssemblyAI Universal-Streaming + the real LLM Gateway binder, not a mock) before this was written. This is the script for the "live demo" segment of `docs/submission/video-script.md`'s Shot 3 — read that file for the surrounding shot list; this file is only the word-for-word part.

## How this was verified

Every line below was synthesized with Windows SAPI text-to-speech and streamed through the actual `BookingSession` + `StreamSession` pipeline (`src/sayless/session.py`, `src/sayless/stream.py`) — the same code path `app/server.py` runs — end to end, in one continuous session, exactly like one real phone call. The exact agent replies quoted below are copied from that run, not invented. Two things worth knowing before you record:

- **Turn-splitting on pauses.** A pause after a leading word (e.g. "Hi," then a beat) can get cut off as its own turn by AssemblyAI's end-of-turn detector, before you finish the sentence. Say each line in one breath, no pause after the first word.
- **Some binder variance.** The LLM Gateway binder is not 100% deterministic turn to turn. In testing, the "two p.m." line was accepted immediately most of the time, but once came back as a one-word confirmation ("two pm?") instead. Both are correct, real behavior — if that happens, just say "yes" and move on. Do one practice run before the real recording so you've seen your own voice through it at least once.

## Setup

1. Start the server: `uvicorn app.server:app --reload`, or `docker run -p 8000:8000 -e ASSEMBLYAI_API_KEY=... say-less` (see the README's Deploy section). Don't record against the Vercel deployment: its WebSocket round trip does not complete, so the agent never replies.
2. Open the page, grant microphone permission.
3. Have a quiet-ish room; you don't need silence, just no other speech in the background.
4. Do one silent practice run through the script below before recording for real.

## The script

Hold the key, say the line, release, wait for the agent's reply (spoken aloud via the browser and shown in the **Readback** panel), then proceed to the next line.

| # | Say this | Field | What the agent should do |
|---|---|---|---|
| 1 | "I would like to book a shampoo please." | service (deliberately not on the menu) | Catches it — **not** a mishearing, a membership check. Move: `restricted_request`. Says: **"Which service?"** |
| 2 | "A haircut please." | service | Accepts. Move: `accept`. Says: **"And the day?"** |
| 3 | "Tuesday please." | day | Accepts. Move: `accept`. Says: **"And the time?"** |
| 4 | "Two p.m. please." | time | Usually accepts and says **"And the last name?"**. If instead it asks **"two pm?"**, just say "Yes" — then it continues to "And the last name?" |
| 5 | "My last name is Bennett." | surname | Accepts. Move: `accept`. Says the readback: **"haircut on Tuesday at two pm for Bennett — correct?"** |
| 6 | "Yes, that's correct." | confirmation | Books it. Says: **"Booked. See you then."** |

That's the whole call: one deliberate repair, one clean multi-field completion, six turns, under a minute of audio.

### Why line 1 is "shampoo," specifically

This is the thesis of the whole project, made visible in the first ten seconds: the agent isn't guessing at a word it half-heard — "shampoo" transcribes perfectly cleanly (every word at ≥0.83 confidence in testing) and still gets caught, because it simply isn't a member of the service field's allowed set. That's the "confidence lies, membership doesn't" claim from the README and pitch deck, demonstrated live rather than asserted. It's also the most reliable repair to reproduce on camera: a genuine mishearing (the "Tuesday or Thursday?" moment in the teaser image) depends on acoustic luck — real noise, a real accent quirk — that a clean scripted take can't guarantee. An out-of-menu word triggers the mechanism every time, regardless of mic quality.

### On-screen, for reference

While recording, the three panels update live:

- **The ticker** — the live transcript, word by word, with low-confidence words flagged in amber. On line 1 every word should read clean/high-confidence — worth calling out on camera that this repair fires *despite* clean transcription.
- **The readback** — the agent's question, the move badge (amber while unresolved, green once `accept`/`readback`), the four booking fields filling in one at a time, and the raw booking JSON at the bottom.
- **The ledger** — the allowed values per field, for anyone watching to see "shampoo" genuinely isn't on the list.

## Full expected transcript (one clean take)

```
You:   "I would like to book a shampoo please."
Agent: "Which service?"
You:   "A haircut please."
Agent: "And the day?"
You:   "Tuesday please."
Agent: "And the time?"
You:   "Two p.m. please."
Agent: "And the last name?"
You:   "My last name is Bennett."
Agent: "haircut on Tuesday at two pm for Bennett — correct?"
You:   "Yes, that's correct."
Agent: "Booked. See you then."
```

## If a line doesn't land as scripted

This is a real system calling a real API, not a canned recording — occasionally a line will come back differently than the table above (a different confidence read, an extra confirmation step). Don't panic-cut the recording: either let the real repair ladder play out (it's still an honest demonstration of the mechanism) and narrate what happened, or pause and retry that one line. What you should *not* do is edit the agent's spoken replies in post — the whole pitch is that this is live and real; a doctored transcript undercuts it.
