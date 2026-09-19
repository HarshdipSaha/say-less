"""Automated Playwright demo recorder for Say Less.
Records 1920x1080 screencast with injected cursor, click ripple, CSS zoom,
and scene boundary markers for automated composition.

Run: python record.py
"""
import base64
import json
import os
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
RAW_DIR = HERE / "raw"
RAW_DIR.mkdir(exist_ok=True)
AUDIO_DIR = HERE / "caller_audio"

CHROME_EXE = r"C:\Users\HARSHDIP\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe"
LIVE_URL = "https://say-less-xh3x.onrender.com"
W, H = 1920, 1080
FLASH_S = 0.5

CURSOR_JS = r"""
(() => {
  try {
    const getRoot = () => document.getElementById('root') || document.body;
    window.__zoom = (x, y, s) => {
      const root = getRoot();
      root.style.transition = 'transform .7s cubic-bezier(.22,.61,.36,1)';
      root.style.transformOrigin = x + 'px ' + y + 'px';
      root.style.transform = 'scale(' + s + ')';
    };
    window.__unzoom = () => {
      const root = getRoot();
      root.style.transform = 'none';
    };
    window.__flash = (ms) => {
      const f = document.createElement('div');
      f.id = '__flash_marker';
      f.style.cssText = 'position:fixed;left:0;top:0;width:56px;height:56px;background:#ff00ff;z-index:2147483647;pointer-events:none;';
      document.documentElement.appendChild(f);
      setTimeout(() => f.remove(), ms);
    };

    let cur = null;
    const ensure = () => {
      if (cur && cur.isConnected) return cur;
      if (!document.documentElement) return null;
      cur = document.createElement('div');
      cur.id = '__cur';
      cur.style.cssText = 'position:fixed;z-index:2147483646;width:24px;height:24px;pointer-events:none;' +
        'border-radius:50%;background:rgba(108,92,231,.95);border:2px solid #fff;' +
        'box-shadow:0 0 0 3px rgba(0,0,0,.35),0 4px 16px rgba(108,92,231,.8);transform:translate(-50%,-50%);left:-100px;top:-100px;' +
        'transition:left .05s linear, top .05s linear;';
      document.documentElement.appendChild(cur);
      return cur;
    };

    window.addEventListener('mousemove', e => {
      const el = ensure();
      if (!el) return;
      el.style.left = e.clientX + 'px';
      el.style.top = e.clientY + 'px';
    }, true);

    window.addEventListener('mousedown', e => {
      if (!document.documentElement) return;
      const r = document.createElement('div');
      r.style.cssText = 'position:fixed;z-index:2147483645;left:' + e.clientX + 'px;top:' + e.clientY + 'px;width:24px;height:24px;' +
        'border-radius:50%;border:3px solid rgba(70,227,183,.9);transform:translate(-50%,-50%) scale(1);pointer-events:none;' +
        'transition:transform .45s ease-out, opacity .45s ease-out;opacity:1;';
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => {
        r.style.transform = 'translate(-50%,-50%) scale(3.2)';
        r.style.opacity = '0';
      });
      setTimeout(() => r.remove(), 500);
    }, true);

    document.addEventListener('DOMContentLoaded', ensure);
  } catch (e) { console.error('cursor init failed', e); }
})();
"""

SEND_AUDIO_JS = r"""
async (base64Wav) => {
  for (let i = 0; i < 40 && ws.readyState !== 1; i++) {
    await new Promise(r => setTimeout(r, 250));
  }
  if (ws.readyState !== 1) {
    return { error: 'ws not open', state: ws.readyState };
  }

  const binary = atob(base64Wav);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

  const dv = new DataView(bytes.buffer);
  const td = new TextDecoder('ascii');
  let off = 12, dOff = -1, dSize = 0;
  while (off < bytes.byteLength) {
    const id = td.decode(new Uint8Array(bytes.buffer, off, 4));
    const sz = dv.getUint32(off + 4, true);
    if (id === 'data') { dOff = off + 8; dSize = sz; break; }
    off += 8 + sz + (sz % 2);
  }
  const pcm = new Uint8Array(bytes.buffer, dOff, dSize);

  // Visually activate push-to-talk button
  const key = document.getElementById('key');
  const status = document.getElementById('status');
  if (key) key.classList.add('live');
  if (status) { status.textContent = 'Transmitting…'; status.dataset.tone = 'live'; }

  // Send in 3200-byte (100ms) frames
  for (let i = 0; i < pcm.length; i += 3200) {
    ws.send(pcm.slice(i, i + 3200).buffer);
    await new Promise(r => setTimeout(r, 100));
  }

  if (key) {
    key.classList.remove('live');
    key.classList.add('thinking');
  }
  if (status) {
    status.textContent = 'Reading back…';
    status.dataset.tone = 'live';
  }

  // Stream faint noise frames to keep session alive until agent responds
  const noise = new Int16Array(1600);
  const agentPrev = document.getElementById('agent-text')?.textContent || '';
  for (let i = 0; i < 240; i++) {
    for (let j = 0; j < noise.length; j++) noise[j] = (Math.random() * 60 - 30) | 0;
    if (ws.readyState === 1) ws.send(noise.buffer.slice(0));
    await new Promise(r => setTimeout(r, 100));
    const cur = document.getElementById('agent-text')?.textContent || '';
    if (!document.getElementById('readback').hidden && cur !== agentPrev && cur.length > 0) {
      break;
    }
  }

  return {
    ticker: document.getElementById('ticker')?.innerText,
    agentText: document.getElementById('agent-text')?.textContent,
    move: document.getElementById('move')?.textContent,
    raw: document.getElementById('raw')?.textContent
  };
}
"""


def load_wav_b64(name: str) -> str:
    path = AUDIO_DIR / f"{name}.wav"
    return base64.b64encode(path.read_bytes()).decode("ascii")


def main():
    scenes = []
    t0 = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_EXE,
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": W, "height": H},
            color_scheme="dark"
        )
        page = ctx.new_page()
        page.add_init_script(CURSOR_JS)
        page.set_default_timeout(60000)

        mx, my = 960.0, 540.0

        def move(x, y, steps=25):
            nonlocal mx, my
            page.mouse.move(x, y, steps=steps)
            mx, my = x, y

        def hold(seconds):
            end = time.time() + seconds
            k = 0
            while time.time() < end:
                k += 1
                page.mouse.move(mx + (1 if k % 2 else -1), my, steps=1)
                time.sleep(0.2)

        def mark(name):
            page.evaluate("(ms) => window.__flash(ms)", int(FLASH_S * 1000))
            scenes.append({"name": name, "t": round(time.time() - t0, 3)})
            print(f"[{scenes[-1]['t']:7.2f}] MARK -> {name}", flush=True)
            hold(FLASH_S + 0.3)

        def zoom(loc, s=1.4, dwell=2.0):
            box = loc.bounding_box()
            if not box:
                return
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            page.evaluate("([x,y,s]) => window.__zoom(x,y,s)", [x, y, s])
            hold(dwell)
            page.evaluate("() => window.__unzoom()")
            hold(0.6)

        try:
            # S0: Intro slide
            page.goto((HERE / "intro.html").as_uri())
            hold(0.8)
            mark("S0_intro")
            move(960, 500, 30)
            hold(5.0)

            # S1: Live Web App & Ledger
            page.goto(LIVE_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#schema .ledger-field", timeout=60000)
            hold(1.0)
            mark("S1_interface")

            # Pan cursor to "The ledger" panel
            schema = page.locator("#schema")
            sb = schema.bounding_box()
            if sb:
                move(sb["x"] + sb["width"] / 2, sb["y"] + 60, 25)
                hold(1.2)
                zoom(schema, 1.35, 2.8)

            # Pan cursor to push-to-talk button
            key_btn = page.locator("#key")
            kb = key_btn.bounding_box()
            if kb:
                move(kb["x"] + kb["width"] / 2, kb["y"] + kb["height"] / 2, 25)
                hold(1.2)

            # S2: Out-of-menu Repair (Turn 1: shampoo)
            mark("S2_repair")
            print("Sending Turn 1 (shampoo)...")
            res1 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn1_shampoo"))
            print("Turn 1 Result:", res1)
            hold(1.5)

            # Zoom into Readback and Move badge ("Ask category" / "Which service?")
            readback = page.locator("#readback")
            zoom(readback, 1.45, 3.2)

            # S3: Multi-turn Booking (Turns 2-5)
            mark("S3_turns")

            # Turn 2: haircut
            print("Sending Turn 2 (haircut)...")
            res2 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn2_haircut"))
            print("Turn 2 Result:", res2)
            hold(1.2)

            # Turn 3: tuesday
            print("Sending Turn 3 (tuesday)...")
            res3 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn3_tuesday"))
            print("Turn 3 Result:", res3)
            hold(1.2)

            # Turn 4: two pm
            print("Sending Turn 4 (two pm)...")
            res4 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn4_two_pm"))
            print("Turn 4 Result:", res4)
            hold(1.2)

            # Turn 5: bennett
            print("Sending Turn 5 (bennett)...")
            res5 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn5_bennett"))
            print("Turn 5 Result:", res5)
            hold(1.5)

            # Hover over the populated booking fields
            fields = page.locator("#fields")
            fb = fields.bounding_box()
            if fb:
                move(fb["x"] + fb["width"] / 2, fb["y"] + fb["height"] / 2, 20)
                hold(1.2)

            # S4: Confirmation & Booked (Turn 6)
            mark("S4_booked")
            print("Sending Turn 6 (confirm)...")
            res6 = page.evaluate(SEND_AUDIO_JS, load_wav_b64("turn6_confirm"))
            print("Turn 6 Result:", res6)
            hold(1.5)

            # Zoom into the completed booking slip and raw JSON
            zoom(readback, 1.4, 3.5)
            hold(1.0)

            # S5: Outro slide
            page.goto((HERE / "outro.html").as_uri())
            hold(0.8)
            mark("S5_outro")
            move(960, 540, 25)
            hold(6.5)

            mark("END")
            hold(1.0)

        except Exception as e:
            page.screenshot(path=str(HERE / "record_fail.png"))
            print(f"Recording failed: {e}", file=sys.stderr)
            raise

        video_path = page.video.path()
        ctx.close()
        browser.close()

    (HERE / "scenes.json").write_text(
        json.dumps({"video": video_path, "scenes": scenes}, indent=2)
    )
    print("Recorded raw video:", video_path)
    print("Saved scene markers to scenes.json")


if __name__ == "__main__":
    main()
