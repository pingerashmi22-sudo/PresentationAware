/* global Office, SpeechRecognition */

let recognition;
let isListening = false;

Office.onReady(() => {
  console.log("Office.js ready");
});

// ── Start mic ──────────────────────────────────────────
function startListening() {
  const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechAPI) {
    setStatus("❌ Speech recognition not supported in this browser.");
    return;
  }

  recognition = new SpeechAPI();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous = true;

  recognition.onstart = () => {
    isListening = true;
    setStatus("🎤 Listening...");
    document.getElementById("startBtn").style.display = "none";
    document.getElementById("stopBtn").style.display = "block";
  };

  recognition.onresult = async (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    document.getElementById("transcript").innerText = transcript;
    await processWithBackend(transcript);
  };

  recognition.onerror = (e) => setStatus("❌ Error: " + e.error);
  recognition.onend   = () => { if (isListening) recognition.start(); };

  recognition.start();
}

// ── Stop mic ───────────────────────────────────────────
function stopListening() {
  isListening = false;
  recognition && recognition.stop();
  setStatus("⏹ Stopped.");
  document.getElementById("startBtn").style.display = "block";
  document.getElementById("stopBtn").style.display  = "none";
}

// ── Get current slide text via Office.js ───────────────
async function getSlideText() {
  return new Promise((resolve) => {
    Office.context.document.getSelectedDataAsync(
      Office.CoercionType.Text,
      (result) => resolve(result.status === Office.AsyncResultStatus.Succeeded
        ? result.value : "")
    );
  });
}

// ── Send to your Flask backend ─────────────────────────
async function processWithBackend(transcript) {
  setStatus("⚙️ Processing...");
  const slideText = await getSlideText();

  try {
    const res = await fetch("http://localhost:5000/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speech: transcript, slide_text: slideText })
    });

    const data = await res.json();

    // Show keywords
    const kwDiv = document.getElementById("keywords");
    if (data.keywords && data.keywords.length) {
      kwDiv.innerHTML = data.keywords
        .map(k => `<span>${k}</span>`)
        .join("");
    } else {
      kwDiv.innerText = "None detected";
    }

    // Show suggestion & intent
    document.getElementById("suggestion").innerText = data.suggestions?.[0] || "—";
    document.getElementById("intent").innerText     = data.intent || "—";

    setStatus("✅ Done — " + new Date().toLocaleTimeString());
  } catch (err) {
    setStatus("❌ Cannot reach backend. Is Flask running?");
  }
}

// ── Helper ─────────────────────────────────────────────
function setStatus(msg) {
  document.getElementById("status").innerText = "Status: " + msg;
}