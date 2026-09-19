"""Compose the final narrated, subtitled demo from the raw screencast.

Inputs:
  scenes.json     - from record.py (raw video path + scene marks)
  narration.json  - narration segments & voice config
Outputs:
  tts/<scene>.mp3 + tts/<scene>.srt   (edge-tts, word-timed subtitles)
  clips/<scene>.mp4                   (trimmed, padded, subtitled with audio)
  say-less-demo.mp4                   (crossfaded, loudness-normalized)

Run: python compose.py
"""
import asyncio
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
TTS_DIR = HERE / "tts"
CLIPS_DIR = HERE / "clips"
TTS_DIR.mkdir(exist_ok=True)
CLIPS_DIR.mkdir(exist_ok=True)

FPS = 30
XF = 0.5  # Crossfade duration in seconds
HOLD_TAIL = 0.6  # Silence after narration inside a scene

SUB_STYLE = (
    "FontName=Segoe UI,FontSize=22,PrimaryColour=&H00F0F3F6,OutlineColour=&H00000000,"
    "BackColour=&H88090A0F,BorderStyle=4,Outline=1,Shadow=0,Alignment=2,MarginV=44,Bold=1,Spacing=0.2"
)


def run(cmd, **kw):
    kw.setdefault("cwd", str(HERE))
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("COMMAND FAILED:", " ".join(map(str, cmd)))
        print(r.stderr[-3000:])
        sys.exit(1)
    return r


def probe_dur(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


def ff_path(p):
    return pathlib.Path(p).relative_to(HERE).as_posix()


MARK_FPS = 20


def detect_marks(video):
    """Detect solid magenta 56x56 flash markers in top-left corner."""
    p = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(video),
            "-vf", f"fps={MARK_FPS},crop=56:56:0:0,scale=1:1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
        ],
        cwd=str(HERE), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if p.returncode != 0:
        print(p.stderr.decode(errors="replace")[-2000:])
        sys.exit(1)

    buf = p.stdout
    hits = []
    for i in range(len(buf) // 3):
        r, g, b = buf[3 * i], buf[3 * i + 1], buf[3 * i + 2]
        if r > 150 and b > 150 and g < 100:  # Magenta
            hits.append(i / MARK_FPS)

    marks, prev = [], -99.0
    for t in hits:
        if t - prev > 1.0:
            marks.append(t)
        prev = t
    return marks


def main():
    sc_file = HERE / "scenes.json"
    nar_file = HERE / "narration.json"

    if not sc_file.exists():
        sys.exit("Error: scenes.json not found. Run record.py first.")
    if not nar_file.exists():
        sys.exit("Error: narration.json not found.")

    sc = json.loads(sc_file.read_text())
    nar = json.loads(nar_file.read_text(encoding="utf-8"))
    video = sc["video"]
    marks = sc["scenes"]
    voice = nar["voice"]

    # Detect in-video markers
    vt = detect_marks(video)
    print("In-video marker timestamps:", [round(t, 2) for t in vt])
    if len(vt) == len(marks):
        marks = [{"name": m["name"], "t": t} for m, t in zip(marks, vt)]
        print("Using precise in-video marker timestamps.")
    else:
        print(f"Warning: detected {len(vt)} markers vs {len(marks)} logged; using logged timestamps.")

    # 1. Verify TTS files exist
    print("\n--- Verifying AI Voiceover & Subtitles ---")
    for name in nar["segments"]:
        mp3 = TTS_DIR / f"{name}.mp3"
        srt = TTS_DIR / f"{name}.srt"
        if not mp3.exists() or mp3.stat().st_size == 0:
            sys.exit(f"Error: missing {mp3}. Please synthesize it first.")
        print(f"Ready: {name} ({probe_dur(mp3):.1f}s)")

    # 2. Cut, pad, subtitle & mux per scene
    print("\n--- Processing Scene Clips ---")
    clips = []
    for i in range(len(marks) - 1):
        name = marks[i]["name"]
        t_start = marks[i]["t"] + 0.8  # Skip flash marker itself
        t_end = marks[i + 1]["t"]
        vdur = max(0.1, t_end - t_start)

        mp3 = TTS_DIR / f"{name}.mp3"
        has_audio = mp3.exists()
        adur = probe_dur(mp3) if has_audio else 0.0

        cap = nar.get("max_video_seconds", {}).get(name)
        speed = 1.0
        if cap and vdur > cap:
            speed = vdur / cap
            vdur = cap

        target = max(vdur, adur + HOLD_TAIL) if has_audio else vdur
        out = CLIPS_DIR / f"{name}.mp4"

        vf = [
            f"trim=start={t_start}:end={t_end}",
            f"setpts=(PTS-STARTPTS)/{speed:.4f}",
            f"tpad=stop_mode=clone:stop_duration={max(0.0, target - vdur):.3f}",
            f"fps={FPS}",
            "format=yuv420p"
        ]

        if has_audio:
            srt_path = TTS_DIR / f"{name}.srt"
            srt_rel = ff_path(srt_path).replace(":", "\\:")
            vf.append(f"subtitles='{srt_rel}':force_style='{SUB_STYLE}'")

        fc = "[0:v]" + ",".join(vf) + "[v];"

        if has_audio:
            fc += f"[1:a]apad,atrim=0:{target:.3f},asetpts=PTS-STARTPTS[a]"
            cmd = [
                "ffmpeg", "-y", "-i", video, "-i", str(mp3),
                "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-t", f"{target:.3f}", str(out)
            ]
        else:
            fc += f"anullsrc=r=48000:cl=stereo,atrim=0:{target:.3f}[a]"
            cmd = [
                "ffmpeg", "-y", "-i", video,
                "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-t", f"{target:.3f}", str(out)
            ]

        run(cmd)
        d = probe_dur(out)
        clips.append((name, out, d))
        print(f"Clip {name}: video {vdur:.1f}s, narration {adur:.1f}s -> total {d:.1f}s")

    # 3. Crossfade concat & loudness normalization
    print("\n--- Assembling Final Crossfaded Video ---")
    inputs = []
    for _, p, _ in clips:
        inputs += ["-i", str(p)]

    fc, vlab, alab = [], "0:v", "0:a"
    off = clips[0][2] - XF
    for i in range(1, len(clips)):
        fc.append(f"[{vlab}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[v{i}]")
        fc.append(f"[{alab}][{i}:a]acrossfade=d={XF}:c1=tri:c2=tri[a{i}]")
        vlab, alab = f"v{i}", f"a{i}"
        off += clips[i][2] - XF

    fc.append(f"[{alab}]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

    final_out = HERE / "say-less-demo.mp4"
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(fc),
        "-map", f"[{vlab}]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_out)
    ]
    run(cmd)
    final_dur = probe_dur(final_out)
    print(f"\nSUCCESS: Generated {final_out} ({final_dur:.1f}s)")


if __name__ == "__main__":
    main()
