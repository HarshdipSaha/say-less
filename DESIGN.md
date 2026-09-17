---
name: Say Less
description: A telegraph operator's read-back ritual for a live voice-repair demo — brass hardware on a signal-dark ground, cream paper for evidence.
colors:
  ground: "#0b1512"
  ground-2: "#102019"
  panel: "#f2ead4"
  panel-2: "#e9dfc4"
  ink: "#1c1a13"
  ink-soft: "#57503e"
  brass: "#c1903f"
  brass-light: "#e0b563"
  brass-dark: "#7c561d"
  amber: "#e08a1e"
  amber-deep-low-confidence: "#6e3f0c"
  confirmed: "#3c7c53"
  confirmed-deep: "#1c4a2f"
  danger: "#b04632"
  danger-deep: "#6e2a1d"
  cream-text: "#ece4cf"
  dim-text: "#9fb6a8"
typography:
  wordmark:
    fontFamily: "Roboto Slab, serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.04em"
  panel-label:
    fontFamily: "Roboto Slab, serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.12em"
  slip-question:
    fontFamily: "Roboto Slab, serif"
    fontSize: "21px"
    fontWeight: 500
    lineHeight: 1.35
  body:
    fontFamily: "Public Sans, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  data:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.6
rounded:
  sm: "2px"
  md: "3px"
  lg: "8px"
  full: "50%"
spacing:
  xs: "6px"
  sm: "12px"
  md: "20px"
  lg: "28px"
components:
  key-control:
    backgroundColor: "{colors.brass}"
    rounded: "{rounded.full}"
    size: "116px"
  move-badge:
    backgroundColor: "{colors.amber}"
    textColor: "#2c1a04"
    rounded: "{rounded.md}"
    padding: "6px 10px"
  move-badge-ok:
    backgroundColor: "{colors.confirmed}"
    textColor: "#eafff1"
  move-badge-danger:
    backgroundColor: "{colors.danger}"
    textColor: "#fff0ec"
---

## Overview

Say Less is a live, real-audio demo of a voice-agent repair mechanism, built for hackathon judges to test with their own microphone in under a minute. The visual world is "Confirm the Signal" — a telegraph operator's read-back ritual — chosen over three alternates (an airport split-flap board, a photographic darkroom, and the category-standard chat-bubble voice-assistant UI) through this skill's concept-seed roll (seed key `899e3d62`, dealt indices 7/3/5). Full direction contract lives in `.impeccable/surfaces/app-static-index-html.md`.

The core idea: the repair ladder (catch → recover → ask small) reads as an operator confirming an uncertain signal, not a chatbot guessing. A brass telegraph key is the push-to-talk control; a paper ticker-tape shows the live per-word transcript; a torn readback slip carries the agent's question, the booking fields, and the raw values; a ledger panel shows the allowed values per field. All four are real signal from the live AssemblyAI/backend pipeline — none is decorative.

## Colors

Restrained-to-committed strategy: a near-black signal-green ground (`ground`) carries the page; warm ledger-cream (`panel`) carries the two paper surfaces (ticker, readback slip); brass is the one committed metal accent for hardware and headings. State color is solid-field, never a tint: amber (`amber`) for every in-repair/uncertain state, green (`confirmed`) for accepted/booked, brick-red (`danger`) for escalation. `amber-deep-low-confidence` (#6e3f0c) is a separately tuned darker amber used only for low-confidence ticker words, picked for a ~6.6:1 contrast margin against its 14%-tinted panel background — do not reuse the plain `amber` value for that text role, it fails contrast there.

## Typography

Three sourced, self-hosted variable fonts (`app/static/fonts/*.woff2`, referenced via local `@font-face`, never a CDN `@import` — a live-judged demo can't depend on a CDN being up): **Roboto Slab** for the wordmark, panel labels, key label, readback question, and move badge (the "ledger/telegram-form" voice); **Public Sans** for body/data-field values; **JetBrains Mono** for the ticker transcript and ledger value lists (a measurement/data role, not a "technical" costume). Body text is 16px; secondary/status text sits at 12–14px; data rows at 11–15px monospace. Keep the wordmark and panel labels in Roboto Slab — don't drift to a system sans for headings.

## Layout

Single scene, `max-width: 1040px`, centered. Desktop: control row is `auto 1fr` (key column, then ticker) side by side; below it the readback slip spans full width, then the ledger grid (`auto-fill, minmax(230px,1fr)`). Under 620px the control row stacks to one column, centered. No fixed/sticky chrome. Ledger value lists and the raw-feed line scroll horizontally on overflow rather than wrapping or truncating with an ellipsis (themed thin scrollbar, brass thumb).

## Elevation & Depth

Depth is real hardware shading, not flat cards: the key control uses layered radial-gradient specular highlight + inset shadows to read as a brass dome, plus an offset drop shadow; its lever and base-plate pseudo-elements carry their own smaller offset shadows so the assembly reads as physically stacked (plate behind, knob on top, lever crossing in front). The readback slip and ticker use a single soft offset+blur shadow against the dark ground, not a hard/zero-offset block shadow (this world never earned a neobrutalist shadow language).

## Shapes

Circular for the key control (`50%`). Small, sharp-ish radii elsewhere (2–3px) — panels read as cut paper/card stock, not soft app chrome. The ticker and readback slip each carry one authored edge treatment instead of a plain rounded rect: the ticker has punch-hole perforation (radial-gradient dots) top and bottom plus a 7%-opacity ruled hairline texture; the readback slip has a torn/deckle top edge (double 45°-gradient zigzag). Both are earned, brief-called-for paper materials — don't add a third distinct edge treatment without a reason, and don't apply either treatment to the ledger cards (they're deliberately the plainer, secondary surface).

## Components

- **`.key` (push-to-talk control):** brass radial-gradient dome, dark center dome (`::after`), a lever bar (`::before`, rotated -3°, overhangs the left edge) and a base plate (`.key-col::before`, dark rounded rect peeking out beneath/behind). States via a `--ring` custom property swapped per class: `.live` (amber, pulsing), `.connecting` (brass), `.thinking` (brass-light), `.booked` (confirmed green), `.trouble` (danger red). Keyboard-operable (Space, held) as well as mouse/touch.
- **`.word` / `.word.low` (ticker transcript):** each word stamps in staggered (`stamp-in` keyframes, ~35ms/word). Low-confidence words (<0.65) get the darker amber text plus a dashed amber underline and a faint amber wash — color is never the only signal.
- **`.move-badge` (repair-move label):** solid-field pill, amber by default (in-repair), `data-kind="ok"` for accept/confirm-booking, `data-kind="danger"` for escalate. Labels are human-readable, not the raw enum (`Name one`, `Offer two`, `Ask category`, `Ask again`, `Confirmed`, `Confirm booking`, `Handed to a human`) — mirrors the pitch deck's own ladder language, keep them in sync if the deck copy ever changes.
- **`.raw-feed` (raw booking JSON):** small monospace line at the foot of the readback slip. Deliberately visually secondary (11px, `ink-soft` color) but never via `opacity` on top of an already-muted color — that compounds below AA contrast. Mute through color/size choice only.
- **`.ledger-field`:** the plainest surface in the system on purpose — flat dark panel, 1px border, no paper material. It's supporting data, not part of the "operator's desk" hero materials.

## Do's and Don'ts

- Do keep every state color a solid field (background-color swap), never a tint/opacity fade — this was an explicit raise on the assigned direction and appears everywhere (move badge, key ring, low-confidence word).
- Do self-host fonts from `app/static/fonts/`; don't reintroduce a Google Fonts `@import`.
- Do treat the ticker, ledger, readback slip, and raw-feed line as one coherent panel set — all four are required, real signal (per `PRODUCT.md`), never decorative or removable for "cleanliness."
- Don't add a fourth paper-edge treatment (torn/perforated) without a reason; two is the system's vocabulary.
- Don't reach for a pulsing circular button anywhere else in this product without the lever+plate hardware cues — a bare glowing orb is exactly the category default this world was built to refuse.
- Don't use `--amber` for low-confidence ticker text; use the separately-tuned `#6e3f0c` (contrast-picked for that specific composited background).
