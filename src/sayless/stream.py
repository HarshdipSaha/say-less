"""Universal-Streaming client, plus an offline replay path so the suite runs
without a network."""
import asyncio, json, os, wave
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import websockets

from .evidence import TurnAccumulator, TurnEvidence

BASE = "wss://streaming.assemblyai.com/v3/ws"
PARAMS = "sample_rate=16000&encoding=pcm_s16le&format_turns=false"
KEEPALIVE_SECONDS = 20


def replay_frames(frames: list[dict]) -> Iterator[TurnEvidence]:
    acc = TurnAccumulator()
    for f in frames:
        if (turn := acc.push(f)) is not None:
            yield turn


def turn_to_dict(t: TurnEvidence) -> dict:
    return {"turn_order": t.turn_order, "transcript": t.transcript,
            "end_of_turn_confidence": t.end_of_turn_confidence,
            "words": [w.__dict__ for w in t.words]}


def turn_from_dict(d: dict) -> TurnEvidence:
    from .evidence import WordEvidence
    return TurnEvidence(d["turn_order"], d["transcript"],
                        d["end_of_turn_confidence"],
                        tuple(WordEvidence(**w) for w in d["words"]))


class TranscriptCache:
    """(audio path, keyterms) -> final turn, persisted so the published numbers
    reproduce from a clean checkout with no API key."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data: dict[str, dict | None] = {}
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    @staticmethod
    def key(audio: Path, keyterms: list[str] | None) -> str:
        return json.dumps([Path(audio).name, sorted(keyterms or [])])

    def get(self, audio: Path, keyterms: list[str] | None):
        k = self.key(audio, keyterms)
        if k not in self.data:
            return False, None                    # miss
        raw = self.data[k]
        return True, (turn_from_dict(raw) if raw else None)

    def put(self, audio: Path, keyterms: list[str] | None, turn) -> None:
        self.data[self.key(audio, keyterms)] = turn_to_dict(turn) if turn else None

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True))


def _clip_terms(terms: list[str]) -> list[str]:
    return [t[:50] for t in terms[:100]]


class StreamSession:
    """Owns one websocket. Audio in, TurnEvidence out."""

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.environ["ASSEMBLYAI_API_KEY"]
        self.ws = None
        self._acc = TurnAccumulator()
        self._keepalive: asyncio.Task | None = None

    async def __aenter__(self) -> "StreamSession":
        self.ws = await websockets.connect(
            f"{BASE}?{PARAMS}", additional_headers={"Authorization": self._key})
        self._keepalive = asyncio.create_task(self._pulse())
        return self

    async def __aexit__(self, *exc) -> None:
        if self._keepalive:
            self._keepalive.cancel()
        if self.ws:
            try:
                await self.ws.send(json.dumps({"type": "Terminate"}))
            except Exception:
                pass
            await self.ws.close()

    async def _pulse(self) -> None:
        """Keeps an idle session alive while nobody is speaking."""
        try:
            while True:
                await asyncio.sleep(KEEPALIVE_SECONDS)
                await self.ws.send(json.dumps({"type": "KeepAlive"}))
        except (asyncio.CancelledError, Exception):
            return

    async def send_audio(self, pcm: bytes) -> None:
        await self.ws.send(pcm)

    async def update_keyterms(self, terms: list[str]) -> None:
        if not terms:
            return
        await self.ws.send(json.dumps({"type": "UpdateConfiguration",
                                       "keyterms_prompt": _clip_terms(terms)}))

    async def turns(self) -> AsyncIterator[TurnEvidence]:
        async for raw in self.ws:
            if isinstance(raw, bytes):
                continue
            msg = json.loads(raw)
            if msg.get("type") == "Termination":
                return
            if (turn := self._acc.push(msg)) is not None:
                yield turn


def read_pcm(path: Path) -> bytes:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == 16000, f"{path} is not 16 kHz"
        assert w.getnchannels() == 1, f"{path} is not mono"
        assert w.getsampwidth() == 2, f"{path} is not 16-bit"
        return w.readframes(w.getnframes())


async def _transcribe_file_once(path: Path,
                                keyterms: list[str] | None) -> TurnEvidence | None:
    pcm = read_pcm(path)
    async with StreamSession() as s:
        if keyterms:
            await s.update_keyterms(keyterms)
        collected: list[TurnEvidence] = []

        async def send():
            step = int(16000 * 0.05) * 2
            for i in range(0, len(pcm), step):
                await s.send_audio(pcm[i:i + step])
                await asyncio.sleep(0.05)
            await s.ws.send(json.dumps({"type": "Terminate"}))

        async def recv():
            async for t in s.turns():
                collected.append(t)

        await asyncio.gather(send(), recv())
        return collected[-1] if collected else None


async def transcribe_file(path: Path,
                          keyterms: list[str] | None = None) -> TurnEvidence | None:
    """Stream one file and return its last finalised turn.

    Retries on a transient connection close (observed in practice: a brief
    concurrent-session limit tripped by back-to-back connections, which
    matters here because the evaluation harness calls this many times in a
    row). A small pacing pause runs before every attempt, including the
    first, so a caller looping over many files doesn't need its own delay.
    """
    last_exc: Exception | None = None
    for attempt in range(4):
        await asyncio.sleep(0.6)
        try:
            return await _transcribe_file_once(path, keyterms)
        except websockets.exceptions.ConnectionClosedError as e:
            last_exc = e
            await asyncio.sleep(2 * (attempt + 1))
    raise last_exc
