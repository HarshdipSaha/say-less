"""Render docs/assets/demo.gif — a clean, dark, product-style demo of the
difference Say Less makes on a misheard day.

Left: a typical agent makes you repeat the whole sentence.
Right: Say Less asks about the one word — "Tuesday or Thursday?" — and books it.

Pure Pillow + Windows system fonts, no external tooling. Run:
    py scripts/make_demo_gif.py            # writes docs/assets/demo.gif
    py scripts/make_demo_gif.py --still    # writes docs/assets/demo_still.png
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# --- dark palette (GitHub-dark inspired) ------------------------------------
BG        = (13, 16, 22)
PANEL     = (22, 27, 34)
BORDER    = (44, 51, 62)
TXT       = (230, 237, 243)
MUTED     = (139, 148, 158)
FAINT     = (85, 95, 108)
AMBER     = (240, 185, 80)
AMBER_BG  = (58, 46, 20)
RED       = (248, 96, 88)
GREEN     = (63, 185, 80)
INDIGO    = (150, 130, 250)
AGENT_BUB = (32, 38, 47)
USER_BUB  = (36, 45, 62)
OFFER_BUB = (40, 36, 70)
DONE_BUB  = (24, 46, 32)

S = 2
W, H = 920, 340

F = "C:/Windows/Fonts/"
def font(name, size):
    return ImageFont.truetype(F + name, size * S)

f_mark  = font("segoeuib.ttf", 20)
f_col   = font("seguisb.ttf", 14)
f_lbl   = font("seguisb.ttf", 11)
f_msg   = font("segoeui.ttf", 16)
f_call  = font("seguisb.ttf", 19)
f_chip  = font("seguisb.ttf", 13)
f_meta  = font("segoeui.ttf", 12)


def R(*v):
    return tuple(int(round(x * S)) for x in v)


def rr(d, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(R(*box), radius=int(radius * S), fill=fill,
                        outline=outline, width=int(width * S))


def tx(d, xy, s, fnt, fill, anchor="la"):
    d.text((int(xy[0] * S), int(xy[1] * S)), s, font=fnt, fill=fill, anchor=anchor)


def tl(d, s, fnt):
    return d.textlength(s, font=fnt) / S


def dot(d, cx, cy, r, color):
    d.ellipse(R(cx - r, cy - r, cx + r, cy + r), fill=color)


def check(d, cx, cy, r, color):
    dot(d, cx, cy, r, color)
    pts = [R(cx - .42 * r, cy + .02 * r), R(cx - .12 * r, cy + .34 * r),
           R(cx + .44 * r, cy - .32 * r)]
    d.line([p for xy in pts for p in xy], fill=BG, width=int(2.4 * S), joint="curve")


def mic(d, cx, cy, color):
    rr(d, (cx - 4, cy - 9, cx + 4, cy + 3), 4, fill=color)
    d.arc(R(cx - 7, cy - 4, cx + 7, cy + 7), 20, 160, fill=color, width=int(1.6 * S))
    d.line(R(cx, cy + 7) + R(cx, cy + 11), fill=color, width=int(1.6 * S))
    d.line(R(cx - 4, cy + 11) + R(cx + 4, cy + 11), fill=color, width=int(1.6 * S))


def speaker(d, x, cy, color):
    d.polygon([R(x, cy - 3)[0:2], R(x + 5, cy - 3)[0:2], R(x + 10, cy - 7)[0:2],
               R(x + 10, cy + 7)[0:2], R(x + 5, cy + 3)[0:2], R(x, cy + 3)[0:2]],
              fill=color)
    d.arc(R(x + 11, cy - 6, x + 18, cy + 6), -55, 55, fill=color, width=int(1.6 * S))
    d.arc(R(x + 13, cy - 9, x + 23, cy + 9), -55, 55, fill=color, width=int(1.4 * S))


def waveform(d, x0, x1, cy, color, seed=(4, 10, 6, 15, 22, 12, 7, 17, 25, 14, 9, 5, 13, 8)):
    n = len(seed)
    step = (x1 - x0) / n
    for i, h in enumerate(seed):
        bx = x0 + i * step
        rr(d, (bx, cy - h / 2, bx + step * 0.5, cy + h / 2), step * 0.25, fill=color)


def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tl(d, t, fnt) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def bubble(d, col_x, colw, top, text, *, side, fill, tcolor=TXT, outline=None,
           highlight=None, prefix_check=False):
    padx, pady, lh = 13, 9, 21
    maxw = colw - 34
    lines = wrap(d, text, f_msg, maxw - (18 if prefix_check else 0))
    tw = max(tl(d, ln, f_msg) for ln in lines)
    bw = tw + padx * 2 + (18 if prefix_check else 0)
    bh = len(lines) * lh + pady * 2 - 3
    bx = col_x if side == "L" else col_x + colw - bw
    rr(d, (bx, top, bx + bw, top + bh), 12, fill=fill, outline=outline,
       width=2 if outline else 1)
    tx0 = bx + padx
    if prefix_check:
        check(d, bx + padx + 6, top + bh / 2, 7, GREEN)
        tx0 += 20
    ty = top + pady
    for ln in lines:
        if highlight and highlight in ln:
            pre, _, post = ln.partition(highlight)
            x = tx0
            tx(d, (x, ty), pre, f_msg, tcolor); x += tl(d, pre, f_msg)
            hw = tl(d, highlight, f_msg)
            rr(d, (x - 2, ty - 1, x + hw + 2, ty + 19), 4, fill=AMBER_BG)
            tx(d, (x, ty), highlight, f_msg, AMBER); x += hw
            tx(d, (x, ty), post, f_msg, tcolor)
        else:
            tx(d, (tx0, ty), ln, f_msg, tcolor)
        ty += lh
    return top + bh


def chip(d, col_x, top, text, color, bg):
    w = tl(d, text, f_chip)
    rr(d, (col_x, top, col_x + w + 26, top + 26), 13, fill=bg)
    dot(d, col_x + 13, top + 13, 3.5, color)
    tx(d, (col_x + 22, top + 5), text, f_chip, color)


def render(step):
    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    # caller card (the shared, misheard audio)
    rr(d, (22, 22, W - 22, 92), 14, fill=PANEL, outline=BORDER, width=1)
    dot(d, 48, 57, 15, (30, 30, 44))
    mic(d, 48, 57, INDIGO)
    tx(d, (72, 34), "CALLER", f_lbl, MUTED)
    # transcript with the misheard day
    x = 72
    for word, hl in [("Book", 0), ("me", 0), ("for", 0), ("Thursday", 1), ("please", 0)]:
        if hl:
            wwd = tl(d, word, f_call)
            rr(d, (x - 3, 52, x + wwd + 3, 78), 5, fill=AMBER_BG)
            tx(d, (x, 54), word, f_call, AMBER)
            x += wwd + tl(d, " ", f_call)
        else:
            tx(d, (x, 54), word, f_call, TXT)
            x += tl(d, word + " ", f_call)
    speaker(d, W - 210, 57, MUTED)
    waveform(d, W - 176, W - 44, 57, INDIGO)

    if step < 1:
        return img

    # columns
    gap, m = 22, 22
    colw = (W - 2 * m - gap) / 2
    LX, RX = m, m + colw + gap
    cy = 112
    dot(d, LX + 7, cy + 6, 4, FAINT)
    tx(d, (LX + 20, cy), "Typical agent", f_col, MUTED)
    dot(d, RX + 7, cy + 6, 4, INDIGO)
    tx(d, (RX + 20, cy), "Say Less", f_col, TXT)

    y0 = 138
    # LEFT
    ly = y0
    if step >= 2:
        ly = bubble(d, LX, colw, ly, "Sorry, I didn't catch that \u2014 could you say the whole thing again?",
                    side="L", fill=AGENT_BUB) + 10
    if step >= 3:
        ly = bubble(d, LX, colw, ly, "Book me for Thursday at three.",
                    side="R", fill=USER_BUB) + 12
    if step >= 5:
        chip(d, LX, ly, "6 words to fix one slip", RED, (46, 26, 26))

    # RIGHT
    ry = y0
    if step >= 2:
        ry = bubble(d, RX, colw, ry, "Tuesday or Thursday?",
                    side="L", fill=OFFER_BUB, outline=INDIGO) + 10
    if step >= 3:
        ry = bubble(d, RX, colw, ry, "Thursday.", side="R", fill=USER_BUB) + 10
    if step >= 4:
        ry = bubble(d, RX, colw, ry, "Booked \u2014 Thursday, 3 pm.",
                    side="L", fill=DONE_BUB, prefix_check=True) + 12
    if step >= 5:
        chip(d, RX, ry, "1 word", GREEN, (22, 44, 28))

    return img


def build_frames():
    frames, durs = [], []

    def add(im, ms):
        frames.append(im); durs.append(ms)

    def xfade(a, b, n=3, ms=42):
        for i in range(1, n + 1):
            add(Image.blend(a, b, i / (n + 1)), ms)

    holds = {0: 650, 1: 450, 2: 1150, 3: 1050, 4: 1050, 5: 2600}
    prev = None
    for step in range(6):
        cur = render(step)
        if prev is not None:
            xfade(prev, cur)
        add(cur, holds[step])
        prev = cur
    return frames, durs


def down(im):
    return im.resize((W, H), Image.LANCZOS)


def main():
    if "--still" in sys.argv:
        down(render(5)).save(OUT / "demo_still.png")
        print("wrote", OUT / "demo_still.png")
        return

    frames, durs = build_frames()
    frames = [down(f) for f in frames]

    master = Image.new("RGB", (W, H * 3), BG)
    master.paste(frames[-1], (0, 0))
    master.paste(frames[len(frames) // 2], (0, H))
    master.paste(frames[0], (0, 2 * H))
    pal = master.quantize(colors=220, method=Image.MEDIANCUT, dither=Image.NONE)
    pf = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]

    p = OUT / "demo.gif"
    pf[0].save(p, save_all=True, append_images=pf[1:], loop=0, duration=durs,
               disposal=2, optimize=True)
    print(f"wrote {p}  ({len(pf)} frames, {p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
