# Automated Live Demo Video Pipeline

This directory contains an automated recording and video composition pipeline for **Say Less**, built using the same architecture as CineSignal:

1. **Playwright Screencast** (`record.py`) driving the live deployed app at `https://say-less-xh3x.onrender.com` in 1080p.
2. **Dynamic Injections:**
   - Smooth floating cursor and click ripples.
   - Cinematic CSS zoom-ins into the Ticker, The Ledger, and the Readback slip.
   - Top-left corner magenta flash markers (`#ff00ff`) for frame-accurate scene sync.
3. **Live Audio Driving:**
   - Automatically streams 16kHz PCM audio frames into the page's WebSocket (`ws`).
   - Simulates caller speech for all 6 conversation turns (demonstrating the out-of-menu `shampoo` repair, multi-slot fill, and full readback).
4. **AI Voiceover & Subtitles** (`compose.py`):
   - Generates natural, studio-quality narration using `edge-tts` (`en-US-AndrewNeural`).
   - Generates word-accurate `.srt` subtitles and burns them onto the video with Segoe UI.
   - Smooth video crossfades (`xfade`) and audio crossfades (`acrossfade`).
   - EBU R128 loudness normalization (`loudnorm`).

---

## Files

- [run_all.ps1](run_all.ps1) / [run_all.bat](run_all.bat): Runs the entire pipeline in one click.
- [prepare_audio.py](prepare_audio.py): Synthesizes caller audio turns into 16kHz WAV files.
- [record.py](record.py): Playwright automated recording script.
- [compose.py](compose.py): Video assembly, subtitles, voiceover, and crossfade stitching.
- [narration.json](narration.json): Voiceover script per scene.
- [intro.html](intro.html): Branded 1080p opening title card.
- [outro.html](outro.html): Architecture, benchmark stats, and repository links closing card.

---

## How to Run

### One-Click (PowerShell)
```powershell
cd "docs\video"
.\run_all.ps1
```

### Manual Steps
```bash
cd "docs/video"
python prepare_audio.py
python record.py
python compose.py
```

The final output is saved to `docs/video/say-less-demo.mp4`.
