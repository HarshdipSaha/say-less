const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
ws.binaryType = "arraybuffer";
const $ = (id) => document.getElementById(id);
let ctx, node, talking = false;

ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);

  if (msg.type === "schema") {
    $("schema").innerHTML = Object.entries(msg.fields).map(([name, values]) =>
      `<div class="field"><b>${name}</b> <span>${values.join(", ")}</span></div>`
    ).join("");
  }

  if (msg.type === "turn") {
    $("words").innerHTML = msg.words.map(w => {
      const cls = w.confidence < 0.65 ? "low" : "ok";
      return `<span class="w ${cls}" title="confidence ${w.confidence}, revised ${w.revisions}x">${w.text}</span>`;
    }).join(" ");
  }

  if (msg.type === "agent") {
    $("agent").textContent = msg.text;
    $("values").textContent = JSON.stringify(msg.values, null, 2);
    $("move").textContent = `repair move: ${msg.move}`;
    speechSynthesis.speak(new SpeechSynthesisUtterance(msg.text));
  }
};

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
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } });
  ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  node = ctx.createScriptProcessor(4096, 1, 1);
  node.onaudioprocess = (e) => {
    if (!talking || ws.readyState !== WebSocket.OPEN) return;
    ws.send(toPcm16(e.inputBuffer.getChannelData(0), ctx.sampleRate));
  };
  src.connect(node);
  node.connect(ctx.destination);
}

const down = async (e) => { e.preventDefault(); await start(); talking = true; $("ptt").classList.add("live"); };
const up = () => { talking = false; $("ptt").classList.remove("live"); };
$("ptt").addEventListener("mousedown", down);
$("ptt").addEventListener("mouseup", up);
$("ptt").addEventListener("touchstart", down, { passive: false });
$("ptt").addEventListener("touchend", up);
