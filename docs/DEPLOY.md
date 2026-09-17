# Deploying Say Less

The live demo holds one WebSocket open for the whole call, so it needs a host that runs a normal, always-on server process.

## What doesn't work (checked 2026-09-17)

| Host | Result |
|---|---|
| Vercel | Page loads, but the agent's reply never reaches the browser over the WebSocket. |
| Hugging Face Spaces | Docker Spaces are now paid-only on free accounts, and CPU Basic can't be selected. Only Gradio/ZeroGPU is free, and that can't run this server. |
| Koyeb | New services are blocked ("Koyeb is joining Mistral"). |
| Replit | Asks for a card. |

## Recommended: Render (free web service)

The repo already has `render.yaml` and a `Dockerfile`.

1. Go to https://dashboard.render.com and sign in with GitHub.
2. Click **New +** → **Web Service**.
3. Connect GitHub if asked, then pick the **HarshdipSaha/say-less** repo.
4. Fill in the settings:
   - **Name:** `say-less`
   - **Region:** any
   - **Branch:** `main`
   - **Runtime / Language:** `Docker` (Render finds the `Dockerfile` automatically)
   - **Instance type:** `Free`
5. Under **Environment Variables**, add:
   - Key: `ASSEMBLYAI_API_KEY`
   - Value: your AssemblyAI key
6. Click **Create Web Service**. The first build takes about 3–5 minutes.
7. When the log shows `Uvicorn running on http://0.0.0.0:...`, open the URL Render gives you (`https://say-less-xxxx.onrender.com`).
8. Allow microphone access, hold the key, and speak.

Notes:
- You don't set a port. Render sets `$PORT` and the Dockerfile reads it.
- If Render asks for a card before letting you pick the Free instance, use the fallback below.
- The free tier sleeps after about 15 minutes idle, and the first visit after that takes about 30–60 seconds to wake. Open the URL a minute before you record.

### Alternative on Render: without Docker

In step 4, choose **Runtime: Python 3** and set:
- **Build command:** `pip install -e .`
- **Start command:** `uvicorn app.server:app --host 0.0.0.0 --port $PORT`
- Environment variable `PYTHON_VERSION` = `3.12.6`, plus `ASSEMBLYAI_API_KEY` as above.

Or use **New +** → **Blueprint** and pick the repo; `render.yaml` fills these in, and you only paste the key.

## Fallback: record the demo locally

The app works fully on your own machine. For the hackathon video, this is the most reliable option.

```bash
cd "H:\augsepthacks\assembly-ai hack"
.venv\Scripts\activate
uvicorn app.server:app --port 8000
```

Open http://localhost:8000 and follow `docs/submission/live-demo-script.md`.

Or with Docker (Docker Desktop must be running):

```bash
docker build -t say-less .
docker run -p 8000:8000 -e ASSEMBLYAI_API_KEY=your_key say-less
```

## Other hosts that run the same Dockerfile

Fly.io, Railway, and Google Cloud Run all run it unchanged. Set `ASSEMBLYAI_API_KEY` and let the host set `PORT`. All three currently ask for a card, even on their free allowances.
