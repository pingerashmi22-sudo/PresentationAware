let recognition;
let isListening = false;

function startListening() {
  const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechAPI) {
    setStatus("❌ Not supported in this browser");
    return;
  }

  recognition = new SpeechAPI();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isListening = true;
    document.getElementById("startBtn").style.display = "none";
    document.getElementById("stopBtn").style.display  = "block";
    document.getElementById("dot").classList.add("active");
    setStatus("Listening...");
  };

  recognition.onresult = async (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    document.getElementById("transcript").innerText = transcript;
    await sendToBackend(transcript);
  };

  recognition.onerror = (e) => setStatus("❌ Error: " + e.error);
  recognition.onend   = () => { if (isListening) recognition.start(); };

  recognition.start();
}

function stopListening() {
  isListening = false;
  recognition && recognition.stop();
  document.getElementById("startBtn").style.display = "block";
  document.getElementById("stopBtn").style.display  = "none";
  document.getElementById("dot").classList.remove("active");
  setStatus("Stopped.");
}

async function sendToBackend(transcript) {
  setStatus("⚙️ Processing...");
  try {
    const res = await fetch("http://127.0.0.1:5000/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speech: transcript, slide_text: "" })
    });

    const data = await res.json();

    // Keywords
    const kwDiv = document.getElementById("keywords");
    if (data.keywords && data.keywords.length) {
      kwDiv.innerHTML = data.keywords
        .map(k => `<span class="kw">${k}</span>`)
        .join("");
    } else {
      kwDiv.innerHTML = "<span style='color:#aaa;font-size:13px'>None detected</span>";
    }

    // Suggestion & Intent
    document.getElementById("suggestion").innerText = data.suggestions?.[0] || "—";
    document.getElementById("intent").innerText     = data.intent || "—";

    setStatus("✅ Updated at " + new Date().toLocaleTimeString());
  } catch {
    setStatus("❌ Flask not running! Start python app.py");
  }
}

function setStatus(msg) {
  const statusEl = document.getElementById("status");
  const dot = document.getElementById("dot");
  statusEl.innerHTML = "";
  statusEl.appendChild(dot);
  statusEl.append(" " + msg);
}