# Video script / storyboard (under 3 minutes)

I can't record video myself — this is the shot-by-shot script for whoever does. Split-screen throughout: left pane is a baseline agent, right pane is Say Less, both hearing the *same* noisy audio clip.

## Shot 1 (0:00–0:15) — Cold open, no narration
- Split screen. Same waveform plays into both panes simultaneously.
- Left pane text bubble: **"Sorry, could you repeat that?"**
- Right pane text bubble: **"Tuesday or Thursday?"**
- On-screen counter appears under each pane: "Words re-said: 6" (left) vs "Words re-said: 1" (right).

## Shot 2 (0:15–0:45) — The problem, voiced over the still split screen
- "Voice agents ask the same question every time they mishear you — the least informative one. Humans don't. They ask about the specific word."
- Cut to a simple diagram: the repair ladder (restricted offer → two-way offer → category question → open re-ask), each with an example bubble.

## Shot 3 (0:45–1:30) — Live demo, screen recording of the actual app
- Open the deployed URL. Hold the push-to-talk button, say a booking sentence with a deliberately hard day name.
- Show the "What it heard" panel highlighting the low-confidence word in orange.
- Show the agent asking the specific repair question, live.
- Say "no" to a wrong offer, show the category-question fallback.
- Complete a booking, show the readback confirmation.

## Shot 4 (1:30–2:00) — The technical claim
- Screen recording or code snippet: the `Turn` payload showing `confidence`, `word_is_final`, `end_of_turn_confidence` — annotate "the managed Voice Agent API doesn't give us this."
- One sentence: "The candidate we offer never comes from the recogniser — AssemblyAI gives no alternative hypotheses. It comes from matching against the field's own value list."

## Shot 5 (2:00–2:40) — The numbers
- Cut to the metrics table from `eval_results.json` / the README.
- Voice over the residual bar: "This is what we can't see — a confidently wrong answer that's still a valid value. We report it rather than hide it."

## Shot 6 (2:40–3:00) — Close
- Return to the split-screen opening shot, now with the final counters.
- Text on screen: "Say Less — the agent asks about the word, not the sentence."
- End card: repo URL, live demo URL.

## Notes for whoever records this
- The split-screen shots (1 and 6) can be built from two separate screen recordings of the deployed app, hearing the same pre-recorded noisy clip (one of the files in `corpus/audio/`), edited side by side.
- Keep narration plain — no jargon beyond what shot 4 explicitly defines.
- Under 3 minutes total per the hackathon's submission guidance.
