const $ = (id) => document.getElementById(id);
const body = document.body;
const key = $("key");
const status = $("status");
const ticker = $("ticker");
const readback = $("readback");
const moveEl = $("move");
const agentText = $("agent-text");
const fieldsEl = $("fields");
const schemaEl = $("schema");
const rawEl = $("raw");

const MOVE_LABELS = {
  accept: "Confirmed",
  restricted_offer: "Name one",
  two_way_offer: "Offer two",
  restricted_request: "Ask category",
  open_request: "Ask again",
  escalate: "Handed to a human",
  readback: "Confirm booking",
};
const MOVE_TONE = {
  accept: "ok",
  readback: "ok",
  escalate: "danger",
};

const FIELD_LABELS = { day: "Day", time: "Time", service: "Service", surname: "Last name" };

function setStatus(text, tone) {
  status.textContent = text;
  if (tone) status.dataset.tone = tone; else delete status.dataset.tone;
}

function setKeyState(state) {
  key.classList.remove("live", "connecting", "thinking", "booked", "trouble");
  if (state) key.classList.add(state);
}

let ws;
let ctx, node, talking = false, wsReady = false;

function connect() {
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => { wsReady = true; };

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);

    if (msg.type === "schema") {
      schemaEl.innerHTML = Object.entries(msg.fields).map(([name, values]) => `
        <div class="ledger-field">
          <dt>${FIELD_LABELS[name] || name}</dt>
          <dd>${values.join(", ")}</dd>
        </div>`).join("");
    }

    if (msg.type === "turn") {
      setKeyState("thinking");
      setStatus("Reading back…", "live");
      ticker.innerHTML = msg.words.map((w, i) => {
        const cls = w.confidence < 0.65 ? "word low" : "word";
        return `<span class="${cls}" style="--i:${i}" title="confidence ${w.confidence}, revised ${w.revisions}x">${w.text}</span>`;
      }).join(" ");
    }

    if (msg.type === "agent") {
      readback.hidden = false;
      agentText.textContent = msg.text;

      const kind = msg.move;
      moveEl.textContent = MOVE_LABELS[kind] || kind;
      moveEl.dataset.kind = MOVE_TONE[kind] || "";

      fieldsEl.innerHTML = Object.keys(FIELD_LABELS).map((name) => {
        const val = msg.values[name];
        return `<div><dt>${FIELD_LABELS[name]}</dt><dd class="${val ? "" : "pending"}">${val || "···"}</dd></div>`;
      }).join("");
      rawEl.textContent = JSON.stringify(msg.values);

      if (msg.done) {
        setKeyState("booked");
        setStatus("Booked.", "ok");
      } else if (!talking) {
        setKeyState(null);
        setStatus("");
      }

      speechSynthesis.speak(new SpeechSynthesisUtterance(msg.text));
    }
  };

  ws.onclose = () => {
    wsReady = false;
    setKeyState("trouble");
    setStatus("Line dropped. Reload to reconnect.", "error");
  };
  ws.onerror = () => ws.close();
}
connect();

// Downsample Float32 at ctx.sampleRate to PCM16 at 16 kHz.
function toPcm16(input, inRate) {
  const ratio = inRate / 16000;
  const out = new Int16Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    const s = Math.max(-1, Math.min(1, input[Math.floor(i * ratio)]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out.buffer;
}

async function start() {
  if (ctx) return;
  setKeyState("connecting");
  setStatus("Connecting to the wire…", "live");
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } });
  } catch {
    setKeyState("trouble");
    setStatus("Microphone blocked. Allow access and try again.", "error");
    throw new Error("mic denied");
  }
  ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  node = ctx.createScriptProcessor(4096, 1, 1);
  node.onaudioprocess = (e) => {
    if (!talking || !wsReady) return;
    ws.send(toPcm16(e.inputBuffer.getChannelData(0), ctx.sampleRate));
  };
  src.connect(node);
  node.connect(ctx.destination);
}

async function keyDown() {
  if (talking) return;
  try {
    await start();
  } catch {
    return;
  }
  talking = true;
  key.classList.add("live");
  setStatus("Transmitting…", "live");
}

function keyUp() {
  if (!talking) return;
  talking = false;
  key.classList.remove("live");
}

key.addEventListener("mousedown", (e) => { e.preventDefault(); keyDown(); });
key.addEventListener("mouseup", keyUp);
key.addEventListener("mouseleave", keyUp);
key.addEventListener("touchstart", (e) => { e.preventDefault(); keyDown(); }, { passive: false });
key.addEventListener("touchend", keyUp);

window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat && document.activeElement !== key) return keyDown();
  if (e.code === "Space" && document.activeElement === key) e.preventDefault();
});
window.addEventListener("keyup", (e) => { if (e.code === "Space") keyUp(); });
key.addEventListener("keydown", (e) => { if (e.code === "Space") { e.preventDefault(); keyDown(); } });
key.addEventListener("keyup", (e) => { if (e.code === "Space") keyUp(); });
