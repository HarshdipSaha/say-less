import json
import os
import subprocess
from pathlib import Path

import sys
ROOT = Path(r"H:\augsepthacks\assembly-ai hack")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_real_voice import REAL_MANIFEST

NOISY_DIR = ROOT / "corpus" / "noisy_audio"
NOISY_DIR.mkdir(parents=True, exist_ok=True)
NOISE_FILE = ROOT / "corpus" / "cafe_noise.wav"

def generate_noisy_audio():
    if not NOISE_FILE.exists():
        print(f"Error: {NOISE_FILE} not found. Please wait for the subagent to download it.")
        return False
        
    print(f"Generating noisy dataset in {NOISY_DIR}...")
    
    for item in REAL_MANIFEST:
        clean_audio = item["audio"]
        noisy_audio = NOISY_DIR / clean_audio.name
        
        # We use amix to mix the audio, and set the noise volume slightly lower
        # -t is used so we don't exceed the original audio's length
        cmd = [
            "ffmpeg", "-y",
            "-i", str(clean_audio),
            "-i", str(NOISE_FILE),
            "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2",
            "-ac", "1",
            "-ar", "16000",
            str(noisy_audio)
        ]
        
        print(f"Mixing {clean_audio.name} -> {noisy_audio.name}")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    print("Noisy dataset generation complete!")
    return True

if __name__ == "__main__":
    generate_noisy_audio()
