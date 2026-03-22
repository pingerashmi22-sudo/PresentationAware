if (document.getElementById("pa-panel")) document.getElementById("pa-panel").remove();
if (document.getElementById("pa-kw-toast")) document.getElementById("pa-kw-toast").remove();

var paStyle = document.createElement("style");
paStyle.textContent = "#pa-panel{position:fixed;bottom:20px;right:20px;width:320px;background:#f0f4ff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.2);font-family:Segoe UI,sans-serif;padding:12px;z-index:999999}#pa-header{font-weight:bold;color:#2b579a;font-size:15px;margin-bottom:10px;display:flex;justify-content:space-between}#pa-close{cursor:pointer;color:#999}#pa-panel button{width:100%;padding:9px;border:none;border-radius:8px;font-size:13px;font-weight:bold;cursor:pointer;margin-bottom:8px}#pa-start{background:#2b579a;color:white}#pa-stop{background:#d9534f;color:white}.pa-card{background:white;border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:13px}.pa-label{font-size:10px;color:#888;text-transform:uppercase;margin-bottom:4px}.pa-kw{display:inline-block;background:#FFD700;color:#000;border-radius:4px;padding:3px 9px;margin:3px;font-size:13px;font-weight:bold}#pa-status{font-size:11px;color:#888;text-align:center;margin-top:4px}#pa-action{color:#2b579a;font-weight:bold}#pa-kw-toast{display:none;position:fixed;bottom:120px;right:20px;background:#1a1a1a;color:white;font-size:14px;padding:12px 16px;border-radius:10px;z-index:9999999;box-shadow:0 4px 16px rgba(0,0,0,0.4);max-width:320px;line-height:1.8}.pa-toast-kw{display:inline-block;background:#FFD700;color:#000;font-weight:bold;border-radius:4px;padding:2px 8px;margin:2px;font-size:14px;text-decoration:underline;text-decoration-thickness:2px}";
document.head.appendChild(paStyle);

var toast = document.createElement("div");
toast.id = "pa-kw-toast";
document.body.appendChild(toast);

var panel = document.createElement("div");
panel.id = "pa-panel";
panel.innerHTML = '<div id="pa-header">?? PresentationAware <span id="pa-close">?</span></div><button id="pa-start">? Start Listening</button><button id="pa-stop" style="display:none">? Stop</button><div class="pa-card"><div class="pa-label">YOU SAID</div><div id="pa-transcript">-</div></div><div class="pa-card"><div class="pa-label">? KEYWORDS</div><div id="pa-keywords">-</div></div><div class="pa-card"><div class="pa-label">?? SUGGESTION</div><div id="pa-suggestion">-</div></div><div class="pa-card"><div class="pa-label">?? INTENT</div><div id="pa-intent">-</div></div><div class="pa-card"><div class="pa-label">? ACTION</div><div id="pa-action">-</div></div><div id="pa-status">Idle</div>';
document.body.appendChild(panel);

document.getElementById("pa-close").onclick = function() {
  panel.remove(); toast.remove();
};

var recognition;
var isListening = false;

function showToast(keywords) {
  if (!keywords || keywords.length === 0) return;
  toast.innerHTML = "?? Keywords detected:<br>" +
    keywords.map(function(k) {
      return "<span class='pa-toast-kw'>" + k + "</span>";
    }).join(" ");
  toast.style.display = "block";
  clearTimeout(toast._t);
  toast._t = setTimeout(function() { toast.style.display = "none"; }, 5000);
}

function getCurrentSlide() {
  var m = window.location.href.match(/slide=id\.p(\d+)/);
  return m ? parseInt(m[1]) : 1;
}

function goToSlide(target) {
  var diff = target - getCurrentSlide();
  if (diff === 0) return;
  var key = diff > 0 ? "ArrowRight" : "ArrowLeft";
  var code = diff > 0 ? 39 : 37;
  var i = 0;
  var iv = setInterval(function() {
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key:key, keyCode:code, bubbles:true, cancelable:true}));
    if (++i >= Math.abs(diff)) clearInterval(iv);
  }, 400);
}

function applyAction(intent, targetSlide, keywords) {
  var a = document.getElementById("pa-action");
  if (intent === "next_slide") {
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowRight", keyCode:39, bubbles:true, cancelable:true}));
    a.innerText = "? Moved to next slide";
  } else if (intent === "previous_slide") {
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowLeft", keyCode:37, bubbles:true, cancelable:true}));
    a.innerText = "? Moved to previous slide";
  } else if (intent === "speech" && keywords && keywords.length > 0) {
    showToast(keywords);
    if (targetSlide) {
      goToSlide(targetSlide);
      a.innerText = "? Jumped to slide " + targetSlide;
    } else {
      a.innerText = "? Keywords shown";
    }
  } else {
    a.innerText = "-";
  }
}

document.getElementById("pa-start").onclick = function() {
  var S = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!S) { document.getElementById("pa-status").innerText = "Not supported"; return; }
  recognition = new S();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.onstart = function() {
    isListening = true;
    document.getElementById("pa-start").style.display = "none";
    document.getElementById("pa-stop").style.display = "block";
    document.getElementById("pa-status").innerText = "?? Listening...";
  };
  recognition.onresult = function(e) {
    var t = e.results[e.results.length-1][0].transcript;
    document.getElementById("pa-transcript").innerText = t;
    sendToBackend(t);
  };
  recognition.onerror = function(e) { document.getElementById("pa-status").innerText = "Error: " + e.error; };
  recognition.onend = function() { if (isListening) recognition.start(); };
  recognition.start();
};

document.getElementById("pa-stop").onclick = function() {
  isListening = false;
  if (recognition) recognition.stop();
  document.getElementById("pa-start").style.display = "block";
  document.getElementById("pa-stop").style.display = "none";
  document.getElementById("pa-status").innerText = "Stopped";
};

function sendToBackend(transcript) {
  document.getElementById("pa-status").innerText = "?? Processing...";
  fetch("http://127.0.0.1:5000/process", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({speech: transcript, slide_text: ""})
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    var kd = document.getElementById("pa-keywords");
    kd.innerHTML = data.keywords && data.keywords.length
      ? data.keywords.map(function(k) { return "<span class='pa-kw'>" + k + "</span>"; }).join("")
      : "None detected";
    document.getElementById("pa-suggestion").innerText = data.suggestions && data.suggestions[0] ? data.suggestions[0] : "-";
    document.getElementById("pa-intent").innerText = data.intent || "-";
    document.getElementById("pa-status").innerText = "? " + new Date().toLocaleTimeString();
    applyAction(data.intent, data.target_slide, data.keywords);
  })
  .catch(function() {
    document.getElementById("pa-status").innerText = "? Start Flask: python app.py";
  });
}
