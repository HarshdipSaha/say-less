"""Degrade clean TTS clips into something closer to a hard phone call.

Say Less's gate calls for recording real, hard, noisy human speech. No human
voice was available, so scripts/synthesize.ps1 produced clean synthetic clips
instead, and this script degrades them: a narrowband round-trip (16kHz -> 8kHz
-> 16kHz, simulating a phone codec's bandwidth loss) plus additive noise at a
per-file randomised SNR. This is a documented substitute for real recordings,
not a claim that it reproduces real accented or noisy speech -- see the
README's "Audio corpus" section for what this does and does not establish.

Pure stdlib (wave + audioop), no extra dependency. audioop is present in
Python 3.12 and was removed in 3.13, which is why the project pins 3.12.
"""
import audioop
import random
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "corpus" / "audio" / "_raw"
OUT = ROOT / "corpus" / "audio"
SEED = 20260910  # reproducible degradation, not a security-relevant seed

random.seed(SEED)


def read_pcm16_mono_16k(path: Path) -> bytes:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2
        return w.readframes(w.getnframes())


def write_pcm16_mono_16k(path: Path, pcm: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(pcm)


def narrowband_roundtrip(pcm: bytes) -> bytes:
    """16kHz -> 8kHz -> 16kHz. Approximates a phone codec's bandwidth loss:
    everything above ~4kHz (where consonant distinctions like s/f/th live) is
    discarded and never comes back."""
    down, _ = audioop.ratecv(pcm, 2, 1, 16000, 8000, None)
    up, _ = audioop.ratecv(down, 2, 1, 8000, 16000, None)
    return up


def add_noise(pcm: bytes, snr_db: float) -> bytes:
    """Additive white noise at the given signal-to-noise ratio."""
    signal_rms = audioop.rms(pcm, 2)
    if signal_rms == 0:
        return pcm
    noise_rms = signal_rms / (10 ** (snr_db / 20))
    n_samples = len(pcm) // 2
    noise = bytearray(len(pcm))
    # Simple bounded PRNG noise, biased toward mid-amplitude (avoids harsh clipping).
    scale = noise_rms * 1.6
    for i in range(n_samples):
        v = int(random.gauss(0, scale))
        v = max(-32768, min(32767, v))
        noise[2 * i: 2 * i + 2] = int(v).to_bytes(2, "little", signed=True)
    return audioop.add(pcm, bytes(noise), 2)


def degrade(path: Path, snr_db: float) -> bytes:
    pcm = read_pcm16_mono_16k(path)
    pcm = narrowband_roundtrip(pcm)
    pcm = add_noise(pcm, snr_db)
    return pcm


def main() -> None:
    files = sorted(RAW.glob("*.wav"))
    assert files, f"no raw clips found in {RAW}; run scripts/synthesize.ps1 first"
    for path in files:
        # yes/no and the short *_ans clips stay lighter (a caller enunciates a
        # deliberate one/two-word answer more clearly than a run-on sentence);
        # full sentences (*_t1/_t2) get pushed harder, in the 6-14 dB SNR band,
        # which is rough enough to produce real recognition errors on top of
        # already-clean TTS.
        name = path.stem
        if name in ("yes", "no") or name.endswith("_ans"):
            snr = random.uniform(14, 20)
        else:
            snr = random.uniform(6, 14)
        pcm = degrade(path, snr)
        out_path = OUT / f"{name}.wav"
        write_pcm16_mono_16k(out_path, pcm)
        print(f"{name:<14} snr={snr:5.1f}dB -> {out_path.relative_to(ROOT)}")
    print(f"\ndegraded {len(files)} clips (seed={SEED})")


if __name__ == "__main__":
    main()
