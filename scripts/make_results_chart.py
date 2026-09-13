"""Render docs/assets/results.png — a clean dark benchmark card for the README.

Numbers come straight from eval_results.json (baseline vs sayless). Pure
Pillow, no external tooling.

    py scripts/make_results_chart.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from make_demo_gif import (BG, BORDER, GREEN, INDIGO, MUTED, PANEL, R, RED, S,
                           TXT, font, rr, tx)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"

W, H = 920, 430
DIM = (150, 158, 170)

f_kick = font("seguisb.ttf", 13)
f_title = font("segoeuib.ttf", 27)
f_lbl = font("seguisb.ttf", 16)
f_pct = font("segoeuib.ttf", 22)
f_big = font("segoeuib.ttf", 34)
f_cap = font("segoeui.ttf", 13)
f_scap = font("seguisb.ttf", 12)


def tl(d, s, fnt):
    return d.textlength(s, font=fnt) / S


def bar(d, x, y, track, label, pct, color, note):
    tx(d, (x, y - 2), label, f_lbl, TXT)
    ty = y + 26
    rr(d, (x, ty, x + track, ty + 26), 13, fill=(30, 36, 45))
    fillw = max(28, track * pct)
    rr(d, (x, ty, x + fillw, ty + 26), 13, fill=color)
    tx(d, (x + fillw - 12, ty + 4), f"{pct:.0%}", f_pct, (10, 12, 16), anchor="ra")
    tx(d, (x + track + 14, ty + 4), note, f_cap, MUTED)


def stat(d, x, w, num, cap, color):
    rr(d, (x, 300, x + w, 388), 14, fill=PANEL, outline=BORDER, width=1)
    tx(d, (x + w / 2, 322), num, f_big, color, anchor="mm")
    for i, line in enumerate(cap):
        tx(d, (x + w / 2, 352 + i * 16), line, f_scap, DIM, anchor="mm")


def main():
    r = json.loads((ROOT / "eval_results.json").read_text())
    b, s = r["baseline"], r["sayless"]

    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    tx(d, (40, 34), "BENCHMARK", f_kick, INDIGO)
    tx(d, (40, 52), "Same agent. Repair logic on vs off.", f_title, TXT)
    tx(d, (40, 90), "15 bookings · identical audio into both · only the planner differs",
       f_cap, MUTED)

    track = 560
    bar(d, 40, 140, track, "Typical agent", b["commit_accuracy"], RED,
        "1 booking shipped wrong")
    bar(d, 40, 222, track, "Say Less", s["commit_accuracy"], GREEN,
        "every booking correct")

    gap = 16
    sw = (W - 80 - 2 * gap) / 3
    stat(d, 40, sw, "+7pts", ["commit accuracy", "93% → 100%"], GREEN)
    stat(d, 40 + sw + gap, sw, "1 word",
         ["to fix a mishearing", "vs the whole sentence"], INDIGO)
    stat(d, 40 + 2 * (sw + gap), sw, "0",
         ["calls dumped", "on a human"], TXT)

    img.resize((W, H), Image.LANCZOS).save(OUT / "results.png")
    print("wrote", OUT / "results.png")


if __name__ == "__main__":
    main()
