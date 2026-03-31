// PresentationAware Content Script - Master/Slave Toolbar Architecture

var IS_TOP = (window === window.top);
console.log("🎤 PA Loading... (frame:", IS_TOP ? "TOP" : "IFRAME", ")");

// ===================== STYLES (Injected in all frames) =====================
var paStyle = document.createElement("style");
paStyle.id = "pa-style";
paStyle.textContent = `
  #pa-toolbar {
    position: fixed;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(30, 30, 30, 0.92);
    backdrop-filter: blur(12px);
    border-radius: 28px;
    padding: 6px 14px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.08);
    font-family: 'Segoe UI', system-ui, sans-serif;
    z-index: 2147483647;
    cursor: grab;
    user-select: none;
    transition: box-shadow 0.3s ease;
  }
  #pa-toolbar.pa-listening {
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 0 0 2px rgba(76, 175, 80, 0.6), 0 0 16px rgba(76, 175, 80, 0.2);
  }
  #pa-toolbar .pa-btn {
    width: 34px;
    height: 34px;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    transition: all 0.2s ease;
    background: rgba(255,255,255,0.08);
    color: #ccc;
    padding: 0;
  }
  #pa-toolbar .pa-btn:hover {
    background: rgba(255,255,255,0.18);
    color: #fff;
    transform: scale(1.1);
  }
  #pa-toolbar .pa-btn.pa-active {
    background: #4CAF50;
    color: white;
  }
  #pa-toolbar .pa-btn.pa-stop-btn {
    background: rgba(229, 57, 53, 0.85);
    color: white;
  }
  #pa-toolbar .pa-status-text {
    color: #aaa;
    font-size: 11px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding: 0 4px;
  }
  #pa-toolbar .pa-kw-pill {
    display: inline-block;
    background: rgba(255, 215, 0, 0.2);
    color: #FFD700;
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 10px;
    margin-left: 2px;
  }
  .pa-highlight-mark {
    background-color: #FFD700 !important;
    color: #000 !important;
    font-weight: bold !important;
    border-radius: 2px !important;
    box-shadow: 0 0 6px rgba(255, 215, 0, 0.6) !important;
    padding: 0 2px !important;
  }
`;
document.head.appendChild(paStyle);

// ===================== TOOLBAR UI (Injected in all frames) =====================
if (document.getElementById("pa-toolbar")) document.getElementById("pa-toolbar").remove();

var toolbar = document.createElement("div");
toolbar.id = "pa-toolbar";
toolbar.innerHTML = `
  <button class="pa-btn" id="pa-mic-btn" title="Enable Microphone">🎙️</button>
  <button class="pa-btn" id="pa-start-btn" title="Start Listening">▶️</button>
  <button class="pa-btn pa-stop-btn" id="pa-stop-btn" title="Stop Listening" style="display:none;">⏹️</button>
  <span class="pa-status-text" id="pa-status">Ready</span>
  <span id="pa-kw-container"></span>
`;
// Only append toolbar to iframes that are actually the presentation iframe, OR the top frame
var isPresentFrame = !IS_TOP && (document.body && document.body.classList.toString().indexOf('punch-present') >= 0 || window.location.href.indexOf('/presentation/') >= 0);
if (IS_TOP || isPresentFrame) {
  document.body.appendChild(toolbar);
}

// ===================== DRAG SUPPORT =====================
var isDragging = false, offsetX = 0, offsetY = 0;
toolbar.addEventListener("mousedown", function (e) {
  if (e.target.tagName === "BUTTON") return;
  isDragging = true;
  var rect = toolbar.getBoundingClientRect();
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
});
document.addEventListener("mousemove", function (e) {
  if (!isDragging) return;
  toolbar.style.left = (e.clientX - offsetX) + "px";
  toolbar.style.top = (e.clientY - offsetY) + "px";
  toolbar.style.bottom = "auto";
});
document.addEventListener("mouseup", function () { isDragging = false; });

// ===================== STATE (Master Only) =====================
var recognition = null;
var isListening = false;
var micEnabled = false;

// ===================== UI SYNC FUNCTIONS =====================
function syncUI(state) {
  if (state.micEnabled) document.getElementById("pa-mic-btn").classList.add("pa-active");
  else document.getElementById("pa-mic-btn").classList.remove("pa-active");

  if (state.isListening) {
    document.getElementById("pa-start-btn").style.display = "none";
    document.getElementById("pa-stop-btn").style.display = "inline-flex";
    toolbar.classList.add("pa-listening");
  } else {
    document.getElementById("pa-start-btn").style.display = "inline-flex";
    document.getElementById("pa-stop-btn").style.display = "none";
    toolbar.classList.remove("pa-listening");
  }

  if (state.statusText) {
    document.getElementById("pa-status").innerText = state.statusText;
  }

  if (state.keywordsHtml !== undefined) {
    document.getElementById("pa-kw-container").innerHTML = state.keywordsHtml;
  }
}

function broadcastState(statusText, keywordsHtml) {
  if (!IS_TOP) return;
  var state = {
    micEnabled: micEnabled,
    isListening: isListening,
    statusText: statusText || document.getElementById("pa-status").innerText,
    keywordsHtml: keywordsHtml !== undefined ? keywordsHtml : document.getElementById("pa-kw-container").innerHTML
  };
  syncUI(state);
  document.querySelectorAll('iframe').forEach(function(f) {
    try { if (f.contentWindow) f.contentWindow.postMessage({paAction: "syncUI", state: state}, "*"); } catch(e){}
  });
}

// ===================== MASTER CONTROLS (Top Frame) =====================
function toggleMicTop() {
  if (!IS_TOP) return;
  if (!micEnabled) {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
      stream.getTracks().forEach(function(t){t.stop();});
      micEnabled = true;
      broadcastState("Mic enabled");
    }).catch(function(err) { broadcastState("Mic denied"); });
  } else {
    micEnabled = false;
    if (isListening) stopListeningTop();
    broadcastState("Mic disabled");
  }
}

function startListeningTop() {
  if (!IS_TOP) return;
  if (!micEnabled) return broadcastState("Enable mic first!");
  var S = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!S) return broadcastState("Not supported");
  recognition = new S();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = false;
  
  recognition.onstart = function() { isListening = true; broadcastState("🎤 Listening..."); };
  recognition.onresult = function(e) {
    var t = e.results[e.results.length-1][0].transcript;
    broadcastState("\"" + t.substring(0, 40) + "\"");
    sendToBackend(t);
  };
  recognition.onerror = function(e) { broadcastState("Error: " + e.error); };
  recognition.onend = function() { if (isListening) recognition.start(); };
  recognition.start();
}

function stopListeningTop() {
  if (!IS_TOP) return;
  isListening = false;
  if (recognition) recognition.stop();
  broadcastState("Stopped", "");
  clearHighlights();
  document.querySelectorAll('iframe').forEach(function(f) {
    try { if (f.contentWindow) f.contentWindow.postMessage({paAction: "clearHighlights"}, "*"); } catch(e){}
  });
}

// ===================== BUTTON HANDLERS =====================
document.getElementById("pa-mic-btn").onclick = function() {
  if (IS_TOP) toggleMicTop();
  else window.parent.postMessage({paAction: "cmd_toggleMic"}, "*");
};

document.getElementById("pa-start-btn").onclick = function() {
  if (IS_TOP) startListeningTop();
  else window.parent.postMessage({paAction: "cmd_startListening"}, "*");
};

document.getElementById("pa-stop-btn").onclick = function() {
  if (IS_TOP) stopListeningTop();
  else window.parent.postMessage({paAction: "cmd_stopListening"}, "*");
};

// ===================== BACKEND (Top Frame Only) =====================
function sendToBackend(transcript) {
  broadcastState("⚙️ Processing...");
  fetch("http://127.0.0.1:5000/process", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ speech: transcript, slide_text: "" })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    var kwHtml = "";
    if (data.keywords && data.keywords.length > 0) {
      kwHtml = data.keywords.slice(0, 4).map(function(k) { return '<span class="pa-kw-pill">' + k + '</span>'; }).join("");
    }
    broadcastState("✓ Processed", kwHtml);
    setTimeout(function() { applyAction(data.intent, data.keywords); }, 100);
  }).catch(function() { broadcastState("❌ Backend error"); });
}

// ===================== ACTION HANDLER (Top Frame Only) =====================
function applyAction(intent, keywords) {
  if (intent === "next_slide") {
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowRight", keyCode:39, bubbles:true, cancelable:true}));
    document.querySelectorAll('iframe').forEach(function(f) { try { if (f.contentWindow) f.contentWindow.postMessage({paAction:"navigate", dir:"next"}, "*"); } catch(e){} });
  } else if (intent === "previous_slide") {
    document.body.dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowLeft", keyCode:37, bubbles:true, cancelable:true}));
    document.querySelectorAll('iframe').forEach(function(f) { try { if (f.contentWindow) f.contentWindow.postMessage({paAction:"navigate", dir:"prev"}, "*"); } catch(e){} });
  } else if ((intent === "highlight" || intent === "speech") && keywords && keywords.length > 0) {
    highlightKeywords(keywords);
    document.querySelectorAll('iframe').forEach(function(f) { try { if (f.contentWindow) f.contentWindow.postMessage({paAction:"highlight", kw: keywords}, "*"); } catch(e){} });
  }
}

// ===================== HIGHLIGHTING (Runs in All Frames) =====================
function getSlideElements() {
  var elements = []; var seen = new Set();
  function add(el) { if (!el || seen.has(el) || !el.textContent.trim()) return; seen.add(el); elements.push(el); }
  
  document.querySelectorAll('text, tspan').forEach(add);
  document.querySelectorAll('foreignObject span, foreignObject p, foreignObject div').forEach(function(el) { if (!el.children.length) add(el); });
  
  var w = document.querySelector('.punch-viewer-svgpage, .punch-viewer-content, #workspace, .punch-present-iframe');
  if (w) w.querySelectorAll('span, p, div').forEach(function(el) { if (!el.children.length) add(el); });

  // If top frame, try accessing iframe directly as fallback
  if (IS_TOP) {
    var f = document.querySelector('iframe.punch-present-iframe');
    if (f) {
      try {
        var d = f.contentDocument || f.contentWindow.document;
        if (d) d.querySelectorAll('text, tspan, foreignObject span').forEach(add);
      } catch(e) {}
    }
  }
  return elements;
}

function clearHighlights() {
  document.querySelectorAll('.pa-highlight-mark').forEach(function(el) {
    var t = el.textContent; var p = el.parentNode;
    if (p) { p.replaceChild(document.createTextNode(t), el); p.normalize(); }
  });
  document.querySelectorAll('.pa-highlight-rect').forEach(function(r) { r.remove(); });
  document.querySelectorAll('[data-pa-highlighted="true"]').forEach(function(el) {
    var c = el.getAttribute('data-pa-original-fill');
    var w = el.getAttribute('data-pa-original-font-weight');
    if (c) el.setAttribute('fill', c); else el.removeAttribute('fill');
    if (w) el.setAttribute('font-weight', w); else el.removeAttribute('font-weight');
    el.removeAttribute('data-pa-highlighted');
  });
}

function highlightKeywords(keywords) {
  clearHighlights();
  if (!keywords || !keywords.length) return;
  getSlideElements().forEach(function(elem) {
    var text = elem.textContent.toLowerCase();
    keywords.forEach(function(kw) {
      var k = kw.toLowerCase().trim();
      if (k.length > 1 && text.includes(k)) {
        if (elem.tagName === 'text' || elem.tagName === 'tspan' || elem.tagName === 'TEXT' || elem.tagName === 'TSPAN') {
          if (!elem.getAttribute('data-pa-highlighted')) {
            elem.setAttribute('data-pa-original-fill', elem.getAttribute('fill') || '');
            elem.setAttribute('data-pa-original-font-weight', elem.getAttribute('font-weight') || '');
            elem.setAttribute('data-pa-highlighted', 'true');
            elem.setAttribute('fill', '#000000');
            elem.setAttribute('font-weight', 'bold');
            try {
              var bbox = elem.getBBox();
              var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
              rect.setAttribute('class', 'pa-highlight-rect');
              rect.setAttribute('x', bbox.x - 2); rect.setAttribute('y', bbox.y - 2);
              rect.setAttribute('width', bbox.width + 4); rect.setAttribute('height', bbox.height + 4);
              rect.setAttribute('fill', '#FFD700'); rect.setAttribute('fill-opacity', '0.5'); rect.setAttribute('rx', '2');
              elem.parentNode.insertBefore(rect, elem);
            } catch (e) {}
          }
        } else {
          if (!elem.querySelector('.pa-highlight-mark')) {
            var rx = new RegExp('(' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
            elem.innerHTML = elem.innerHTML.replace(rx, '<span class="pa-highlight-mark">$1</span>');
          }
        }
      }
    });
  });
}

// ===================== CROSS-FRAME MESSAGING =====================
window.addEventListener("message", function(e) {
  if (!e.data) return;
  
  if (IS_TOP) {
    // Top frame receives commands from Slave
    if (e.data.paAction === "cmd_toggleMic") toggleMicTop();
    if (e.data.paAction === "cmd_startListening") startListeningTop();
    if (e.data.paAction === "cmd_stopListening") stopListeningTop();
  } else {
    // Slave iframe receives commands from Master
    if (e.data.paAction === "syncUI") syncUI(e.data.state);
    if (e.data.paAction === "clearHighlights") clearHighlights();
    if (e.data.paAction === "highlight") highlightKeywords(e.data.kw);
    if (e.data.paAction === "navigate") {
      document.body.dispatchEvent(new KeyboardEvent("keydown", {key: e.data.dir==="next"?"ArrowRight":"ArrowLeft", keyCode: e.data.dir==="next"?39:37, bubbles: true, cancelable: true}));
    }
  }
});

console.log("✅ PA Architecture Ready!");