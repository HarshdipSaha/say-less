<div align="center">

# 🎙️ Say Less

### The voice agent that asks about the **one word it missed** — not the whole sentence.

[![License: MIT](https://img.shields.io/badge/License-MIT-A371F7.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![AssemblyAI](https://img.shields.io/badge/AssemblyAI-Universal--Streaming-6C5CE7?style=flat-square)](https://www.assemblyai.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-realtime-009688?style=flat-square&logo=fastapi&logoColor=white)](app/server.py)
[![Tests](https://img.shields.io/badge/tests-89%20passing-3fb950?style=flat-square)](tests/)
[![Hackathon](https://img.shields.io/badge/AssemblyAI-Voice%20Agent%20Hackathon-0d1117?style=flat-square)](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon)

**[How it works](#how-it-works)** · **[The benchmark](#the-benchmark)** · **[Try it](#try-it)**

</div>

<div align="center">
  <img src="docs/assets/demo.gif" alt="Split screen. A caller's day is misheard. The typical agent asks them to repeat the whole sentence; Say Less just asks 'Tuesday or Thursday?' and books it." width="880">
</div>

---

## The 15-second story

You call your dentist. There's traffic behind you, the line is bad. You say *"Thursday."*

The robot says: **"Sorry, I didn't catch that. Could you repeat that?"**

So you say the whole thing again. And it mishears the same hard word again. You start to wish you'd never called.

A **human** receptionist would never do that. They heard *most* of it — they just missed one word. So they ask the obvious question:

> ### "Tuesday or Thursday?"

You say one word. You're booked. That's the entire idea behind **Say Less**.

## How it works

Most agents re-ask on **low confidence** — *"how sure am I about these sounds?"* Say Less asks something smarter: *"does this word actually belong here?"*

For fields with a known list of valid answers — a **day** of the week, a **service** from the menu, a **surname** on the booking — Say Less does three things the moment your turn ends:

| Step | | |
|:---:|---|---|
| **1** | **Catch** | The value it heard isn't on the list — even if the recogniser was *confident*. That's the failure that quietly books the wrong thing. |
| **2** | **Recover** | It finds the closest real menu item by how it *sounds*, not how it's spelled. |
| **3** | **Ask small** | It asks the most specific question it can, and no bigger: |

```
   confident ─────────────────────────────────────────────► unsure
   ┌───────────────┬──────────────────┬───────────────┬───────────────┐
   │ name one       │ offer two         │ ask the group │ ask again     │
   │ "kids cut?"    │ "Tuesday or Thu?" │ "Which day?"   │ "Sorry?"      │
   └───────────────┴──────────────────┴───────────────┴───────────────┘
    ▲ Say Less starts as far left as it can        ▲ every other agent lives here
```

The answer it offers is **never made up**. AssemblyAI's real-time model gives per-word confidence — the raw signal a normal agent throws away — and Say Less pairs it with *your own list of valid answers* to work out what you probably meant. That's why it can say *"Tuesday or Thursday?"* instead of *"huh?"*

## The benchmark

Same agent, run twice on the **same audio** — once with the repair logic on, once off. The only thing that changes is the planner.

<div align="center">
  <img src="docs/assets/results.png" alt="Benchmark: commit accuracy 93% for a typical agent vs 100% for Say Less; one word to fix a mishearing vs the whole sentence; zero calls handed to a human." width="880">
</div>

The gap is one booking a normal agent gets **silently wrong** — it heard something a letter off the menu, never noticed, and booked it anyway. Say Less caught it and fixed it in a single word. It's measured against real recorded calls (a range of accents and devices, plus the public SLURP corpus) alongside a phone-degraded test set — the [full results and per-call records](eval_results.json) are committed and replay with no API key.

> **What that's worth.** At a 93% → 100% accuracy gap, roughly **667 wrong bookings per 10,000 calls** get caught before they ship. At a typical **\$7–12** to have a human clean up one wrong booking ([industry figures, 2026](https://www.retellai.com/blog/call-center-outsourcing-costs)), that's **\$4,700–\$8,000 saved per 10,000 calls** — before you count the customer who got the wrong slot and simply never came back.

## Try it

[Live Link](https://huggingface.co/spaces/Godlyharsh/say-less)

Reproduce every number above with **no API key** — the results replay from committed recordings:

```bash
python -m venv .venv && source .venv/Scripts/activate   # .venv\Scripts\activate on Windows cmd
pip install -e ".[dev]"

pytest -v                              # 89 tests — no network, no key
python -m evalharness.run --offline    # replays the recordings, reprints the benchmark
```

Want the live, talk-to-it demo? Add an AssemblyAI key and run the server:

```bash
cp .env.example .env    # paste your ASSEMBLYAI_API_KEY
uvicorn app.server:app --reload         # open http://localhost:8000 and hold to talk
```

## Built with

**AssemblyAI Universal-Streaming** (real-time speech-to-text with per-word confidence) · **AssemblyAI LLM Gateway** · **FastAPI** · a plain browser push-to-talk front end. Built for the **[AssemblyAI Voice Agent Hackathon](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon)**.

Deeper reading: [the spec](docs/SPEC.md) · [live status & decision log](docs/STATUS.md) · [why it's designed this way](docs/council/verdict.md) · [the research behind it](docs/research-3w-scan.md)

<div align="center">
<br>
<b>Say Less</b> — the agent asks about the word, not the sentence.
</div>
