"""Generates 16kHz mono PCM WAV files for the caller turns using edge-tts + ffmpeg.
Run: python prepare_audio.py
"""
import asyncio
import os
import pathlib
import subprocess
import edge_tts

HERE = pathlib.Path(__file__).parent
AUDIO_DIR = HERE / "caller_audio"
AUDIO_DIR.mkdir(exist_ok=True)

VOICE = "en-US-GuyNeural"  # Clear, natural male caller voice (contrasting with AndrewNeural narrator)

TURNS = [
    ("turn1_shampoo", "I would like to book a shampoo please."),
    ("turn2_haircut", "A haircut please."),
    ("turn3_tuesday", "Tuesday please."),
    ("turn4_two_pm", "Two p.m. please."),
    ("turn5_bennett", "My last name is Bennett."),
    ("turn6_confirm", "Yes, that's correct."),
]


async def gen_turn(name: str, text: str):
    mp3_path = AUDIO_DIR / f"{name}.mp3"
    wav_path = AUDIO_DIR / f"{name}.wav"

    com = edge_tts.Communicate(text, VOICE, rate="+3%")
    await com.save(str(mp3_path))

    # Convert to 16kHz mono 16-bit PCM WAV (AssemblyAI streaming spec)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_path)
        ],
        capture_output=True,
        check=True
    )
    if mp3_path.exists():
        mp3_path.unlink()
    print(f"Generated {wav_path.name}")


async def main():
    print("Synthesizing caller speech turns...")
    for name, text in TURNS:
        await gen_turn(name, text)
    print("All caller audio clips prepared.")


if __name__ == "__main__":
    asyncio.run(main())
