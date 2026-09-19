"""Builds timed multi-voice dialogue audio tracks and matching SRT subtitles
for S2_repair, S3_turns, and S4_booked.

Voices:
- Narrator: en-US-AndrewNeural
- Caller: en-US-GuyNeural
- Agent (Say Less): en-US-JennyNeural
"""
import pathlib
import subprocess

HERE = pathlib.Path(__file__).parent
TTS_DIR = HERE / "tts"
CALLER_DIR = HERE / "caller_audio"
AGENT_DIR = HERE / "agent_audio"


def _fmt(t):
    ms = int(round((t - int(t)) * 1000))
    t = int(t)
    return f"{t // 3600:02}:{(t % 3600) // 60:02}:{t % 60:02},{ms:03}"


def build_track(name: str, total_sec: float, cues: list):
    """
    cues: list of dicts:
    [
      {"offset": 0.5, "audio": path, "speaker": "Narrator", "text": "...", "dur": 3.0}
    ]
    """
    # 1. Generate mixed audio via FFmpeg
    inputs = ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={total_sec:.2f}"]
    filter_parts = []

    for idx, c in enumerate(cues, 1):
        inputs.extend(["-i", str(c["audio"])])
        ms = int(c["offset"] * 1000)
        filter_parts.append(f"[{idx}:a]adelay={ms}|{ms}[a{idx}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(1, len(cues) + 1))
    filter_parts.append(f"[0:a]{mix_inputs}amix=inputs={len(cues)+1}:duration=first:dropout_transition=0[aout]")

    out_mp3 = TTS_DIR / f"{name}.mp3"
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[aout]", "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_mp3)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 2. Generate matching SRT
    srt_lines = []
    for idx, c in enumerate(cues, 1):
        start_str = _fmt(c["offset"])
        end_str = _fmt(c["offset"] + c["dur"])
        speaker = c["speaker"]
        txt = c["text"]
        srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n[{speaker}] {txt}\n")

    out_srt = TTS_DIR / f"{name}.srt"
    out_srt.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"Created {out_mp3.name} and {out_srt.name} ({total_sec:.1f}s)")


def main():
    # S2_repair: 20s
    s2_cues = [
        {"offset": 0.5, "audio": TTS_DIR / "s2_nar_intro.mp3", "dur": 2.8, "speaker": "Narrator", "text": "Watch what happens with an out-of-menu request."},
        {"offset": 4.0, "audio": CALLER_DIR / "turn1_shampoo.wav", "dur": 2.8, "speaker": "Caller", "text": "I would like to book a shampoo please."},
        {"offset": 8.8, "audio": AGENT_DIR / "agent1_which_service.mp3", "dur": 1.8, "speaker": "Say Less", "text": "Which service?"},
        {"offset": 11.5, "audio": TTS_DIR / "s2_nar_outro.mp3", "dur": 7.5, "speaker": "Narrator", "text": "Every word transcribed with high confidence, but caught immediately."},
    ]
    build_track("S2_repair", 20.0, s2_cues)

    # S3_turns: 24s
    s3_cues = [
        {"offset": 0.5, "audio": CALLER_DIR / "turn2_haircut.wav", "dur": 1.8, "speaker": "Caller", "text": "A haircut please."},
        {"offset": 2.8, "audio": AGENT_DIR / "agent2_and_day.mp3", "dur": 1.8, "speaker": "Say Less", "text": "And the day?"},
        {"offset": 5.2, "audio": CALLER_DIR / "turn3_tuesday.wav", "dur": 1.8, "speaker": "Caller", "text": "Tuesday please."},
        {"offset": 7.5, "audio": AGENT_DIR / "agent3_and_time.mp3", "dur": 1.8, "speaker": "Say Less", "text": "And the time?"},
        {"offset": 10.0, "audio": CALLER_DIR / "turn4_two_pm.wav", "dur": 1.8, "speaker": "Caller", "text": "Two p.m. please."},
        {"offset": 12.5, "audio": AGENT_DIR / "agent4_and_name.mp3", "dur": 1.8, "speaker": "Say Less", "text": "And the last name?"},
        {"offset": 15.0, "audio": CALLER_DIR / "turn5_bennett.wav", "dur": 2.0, "speaker": "Caller", "text": "My last name is Bennett."},
        {"offset": 18.0, "audio": AGENT_DIR / "agent5_readback.mp3", "dur": 4.5, "speaker": "Say Less", "text": "haircut on Tuesday at two pm for Bennett — correct?"},
    ]
    build_track("S3_turns", 24.0, s3_cues)

    # S4_booked: 16s
    s4_cues = [
        {"offset": 1.0, "audio": CALLER_DIR / "turn6_confirm.wav", "dur": 1.8, "speaker": "Caller", "text": "Yes, that's correct."},
        {"offset": 3.8, "audio": AGENT_DIR / "agent6_booked.mp3", "dur": 2.0, "speaker": "Say Less", "text": "Booked. See you then."},
        {"offset": 7.0, "audio": TTS_DIR / "s4_nar_outro.mp3", "dur": 6.5, "speaker": "Narrator", "text": "Six turns, one targeted repair, and zero repetition. Confirmed."},
    ]
    build_track("S4_booked", 16.0, s4_cues)


if __name__ == "__main__":
    main()
