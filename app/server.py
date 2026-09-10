"""Demo server. Browser sends PCM16 over a websocket; the server owns the
AssemblyAI connection so the API key never reaches the client."""
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from sayless.schema import BOOKING_SCHEMA
from sayless.session import BookingSession
from sayless.stream import StreamSession

load_dotenv()
app = FastAPI()
STATIC = Path(__file__).parent / "static"


@app.websocket("/ws")
async def ws_endpoint(client: WebSocket) -> None:
    await client.accept()
    session = BookingSession()

    # The front end renders this so the caller can see which values are allowed.
    await client.send_json({
        "type": "schema",
        "fields": {name: list(spec.values)[:40] for name, spec in BOOKING_SCHEMA.items()},
    })

    upstream: StreamSession | None = None
    pump: asyncio.Task | None = None
    try:
        while True:
            chunk = await client.receive_bytes()
            if upstream is None:
                upstream = await StreamSession().__aenter__()      # lazy connect
                await upstream.update_keyterms(session.opening_keyterms())
                pump = asyncio.create_task(_pump_turns(client, session, upstream))
            await upstream.send_audio(chunk)
    except WebSocketDisconnect:
        pass
    finally:
        if pump:
            pump.cancel()
        if upstream:
            await upstream.__aexit__(None, None, None)


async def _pump_turns(client: WebSocket, session: BookingSession,
                      upstream: StreamSession) -> None:
    async for turn in upstream.turns():
        await client.send_json({
            "type": "turn",
            "transcript": turn.transcript,
            "end_of_turn_confidence": turn.end_of_turn_confidence,
            "words": [{"text": w.text, "confidence": round(w.confidence, 3),
                       "revisions": w.revisions} for w in turn.words],
        })
        reply, terms = session.handle_turn(turn)
        if terms:
            await upstream.update_keyterms(terms)
        await client.send_json({
            "type": "agent", "text": reply, "values": session.values,
            "move": session.pending.kind.label if session.pending else "accept",
            "done": session.done,
        })


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
