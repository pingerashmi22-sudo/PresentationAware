// PresentationAware Content Script - Compact Toolbar Version
console.log("🎤 PA Loading...");

// Remove any existing PA elements
if (document.getElementById("pa-toolbar")) document.getElementById("pa-toolbar").remove();
if (document.getElementById("pa-style")) document.getElementById("pa-style").remove();

// ===================== STYLES =====================
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
  #pa-toolbar:hover {
    box-shadow: 0 6px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.12);
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
    line-height: 1;
  }
  #pa-toolbar .pa-btn:hover {
    background: rgba(255,255,255,0.18);
    color: #fff;
    transform: scale(1.1);
  }
  #pa-toolbar .pa-btn.pa-active {
    background: #4CAF50;
    color: white;
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.5);
  }
  #pa-toolbar .pa-btn.pa-stop-btn {
    background: rgba(229, 57, 53, 0.85);
    color: white;
  }
  #pa-toolbar .pa-btn.pa-stop-btn:hover {
    background: #e53935;
  }
  #pa-toolbar .pa-divider {
    width: 1px;
    height: 20px;
    background: rgba(255,255,255,0.15);
    margin: 0 4px;
  }
  #pa-toolbar .pa-status-text {
    color: #aaa;
    font-size: 11px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding: 0 4px;
    transition: color 0.3s;
  }
  #pa-toolbar .pa-status-text.pa-status-active {
    color: #81C784;
  }
  #pa-toolbar .pa-kw-pill {
    display: inline-block;
    background: rgba(255, 215, 0, 0.2);
    color: #FFD700;
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
    margin-left: 2px;
    animation: pa-pill-in 0.3s ease;
  }
  @keyframes pa-pill-in {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
  }
  #pa-toolbar .pa-close-btn {
    width: 22px;
    height: 22px;
    font-size: 12px;
    background: rgba(255,255,255,0.05);
    color: #666;
  }
  #pa-toolbar .pa-close-btn:hover {
    background: rgba(229, 57, 53, 0.3);
    color: #e53935;
  }

  /* Keyword highlight on the slide */
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

// ===================== TOOLBAR HTML =====================
var toolbar = document.createElement("div");
toolbar.id = "pa-toolbar";
toolbar.innerHTML = `
  <button class="pa-btn" id="pa-mic-btn" title="Enable Microphone">🎙️</button>
  <div class="pa-divider"></div>
  <button class="pa-btn" id="pa-start-btn" title="Start Listening">▶️</button>
  <button class="pa-btn pa-stop-btn" id="pa-stop-btn" title="Stop Listening" style="display:none;">⏹️</button>
  <div class="pa-divider"></div>
  <span class="pa-status-text" id="pa-status">Ready</span>
  <span id="pa-kw-container"></span>
  <div class="pa-divider"></div>
  <button class="pa-btn pa-close-btn" id="pa-close-btn" title="Close">✕</button>
`;
document.body.appendChild(toolbar);

// ===================== DRAG SUPPORT =====================
(function () {
  var isDragging = false, offsetX = 0, offsetY = 0;
  toolbar.addEventListener("mousedown", function (e) {
    if (e.target.tagName === "BUTTON") return;
    isDragging = true;
    toolbar.style.cursor = "grabbing";
    var rect = toolbar.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    toolbar.style.transform = "none";
  });
  document.addEventListener("mousemove", function (e) {
    if (!isDragging) return;
    toolbar.style.left = (e.clientX - offsetX) + "px";
    toolbar.style.top = (e.clientY - offsetY) + "px";
    toolbar.style.bottom = "auto";
  });
  document.addEventListener("mouseup", function () {
    isDragging = false;
    toolbar.style.cursor = "grab";
  });
})();

// ===================== STATE =====================
var recognition = null;
var isListening = false;
var micEnabled = false;

// ===================== BUTTON HANDLERS =====================

// Close
document.getElementById("pa-close-btn").onclick = function () {
  clearHighlights();
  if (recognition) { isListening = false; recognition.stop(); }
  toolbar.remove();
};

// Mic button - toggle mic permission
document.getElementById("pa-mic-btn").onclick = function () {
  var btn = document.getElementById("pa-mic-btn");
  if (!micEnabled) {
    // Request mic permission
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      // Got permission, stop the stream (we use SpeechRecognition, not raw audio)
      stream.getTracks().forEach(function (t) { t.stop(); });
      micEnabled = true;
      btn.classList.add("pa-active");
      btn.title = "Microphone Enabled";
      setStatus("Mic enabled");
    }).catch(function (err) {
      setStatus("Mic denied: " + err.message);
    });
  } else {
    micEnabled = false;
    btn.classList.remove("pa-active");
    btn.title = "Enable Microphone";
    setStatus("Mic disabled");
    // Also stop listening if active
    if (isListening) {
      stopListening();
    }
  }
};

// Start button
document.getElementById("pa-start-btn").onclick = function () {
  if (!micEnabled) {
    setStatus("Enable mic first!");
    var micBtn = document.getElementById("pa-mic-btn");
    micBtn.style.animation = "none";
    micBtn.offsetHeight; // trigger reflow
    micBtn.style.animation = "";
    return;
  }
  startListening();
};

// Stop button
document.getElementById("pa-stop-btn").onclick = function () {
  stopListening();
};

// ===================== SPEECH RECOGNITION =====================

function startListening() {
  var S = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!S) { setStatus("Not supported"); return; }

  recognition = new S();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = false;

  recognition.onstart = function () {
    isListening = true;
    document.getElementById("pa-start-btn").style.display = "none";
    document.getElementById("pa-stop-btn").style.display = "flex";
    toolbar.classList.add("pa-listening");
    setStatus("🎤 Listening...", true);
  };

  recognition.onresult = function (e) {
    var t = e.results[e.results.length - 1][0].transcript;
    setStatus("\"" + t.substring(0, 40) + (t.length > 40 ? "..." : "") + "\"");
    sendToBackend(t);
  };

  recognition.onerror = function (e) {
    setStatus("Error: " + e.error);
  };

  recognition.onend = function () {
    if (isListening) recognition.start();
  };

  recognition.start();
}

function stopListening() {
  isListening = false;
  if (recognition) recognition.stop();
  document.getElementById("pa-start-btn").style.display = "flex";
  document.getElementById("pa-stop-btn").style.display = "none";
  toolbar.classList.remove("pa-listening");
  setStatus("Stopped");
  clearHighlights();
  document.getElementById("pa-kw-container").innerHTML = "";
}

function setStatus(text, active) {
  var el = document.getElementById("pa-status");
  if (el) {
    el.innerText = text;
    if (active) {
      el.classList.add("pa-status-active");
    } else {
      el.classList.remove("pa-status-active");
    }
  }
}

// ===================== KEYWORD HIGHLIGHTING ON SLIDES =====================

function getSlideElements() {
  var elements = [];

  // 1. Edit mode: Google Slides uses SVG foreignObject with nested spans inside
  //    The main editor area is inside iframes or directly in the page
  var editSvgTexts = document.querySelectorAll('.punch-viewer-svgpage-svgcontainer text, .punch-viewer-svgpage-svgcontainer tspan');
  editSvgTexts.forEach(function (el) { elements.push(el); });

  // 2. Edit mode: text inside foreignObject / shape text content  
  var shapeTexts = document.querySelectorAll(
    '[class*="sketchy-text-content"] span, ' +
    '.punch-viewer-svgpage g[class*="objectGroup"] text, ' +
    '.punch-viewer-content span, ' +
    '.punch-viewer-content p, ' +
    'g.sketchy-text-content-text tspan'
  );
  shapeTexts.forEach(function (el) { elements.push(el); });

  // 3. General fallback: Any visible text spans in the editor area
  var editorArea = document.querySelector('.punch-viewer-content, .punch-present-iframe');
  if (editorArea) {
    var innerSpans = editorArea.querySelectorAll('span, p');
    innerSpans.forEach(function (el) {
      if (el.textContent && el.textContent.trim().length > 0) {
        elements.push(el);
      }
    });
  }

  // 4. Slideshow / Present mode: content is in an iframe
  var presentIframe = document.querySelector('iframe.punch-present-iframe');
  if (presentIframe) {
    try {
      var iframeDoc = presentIframe.contentDocument || presentIframe.contentWindow.document;
      if (iframeDoc) {
        // SVG text elements
        var svgTexts = iframeDoc.querySelectorAll('text, tspan');
        svgTexts.forEach(function (el) { elements.push(el); });

        // Regular text
        var iframeSpans = iframeDoc.querySelectorAll('span, p, div');
        iframeSpans.forEach(function (el) {
          if (el.textContent && el.textContent.trim().length > 0 && el.children.length === 0) {
            elements.push(el);
          }
        });
      }
    } catch (e) {
      console.log("PA: Cannot access iframe (cross-origin):", e.message);
    }
  }

  // 5. Filmstrip (left panel) - the current slide thumbnail
  var filmstrip = document.querySelectorAll('.punch-filmstrip-thumbnail[aria-selected="true"] span, .punch-filmstrip-thumbnail[aria-selected="true"] tspan');
  filmstrip.forEach(function (el) { elements.push(el); });

  return elements;
}

function highlightKeywords(keywords) {
  console.log("🔍 HIGHLIGHT KEYWORDS:", keywords);
  clearHighlights();

  if (!keywords || keywords.length === 0) return false;

  var highlightedCount = 0;
  var elements = getSlideElements();
  console.log("📝 Found", elements.length, "text elements to search");

  // Also search direct text nodes in the main slide area
  var slideArea = document.querySelector('.punch-viewer-svgpage, .punch-viewer-content');

  elements.forEach(function (elem) {
    if (!elem || !elem.textContent) return;
    var originalText = elem.textContent;

    keywords.forEach(function (keyword) {
      var kw = keyword.toLowerCase().trim();
      if (kw.length < 2) return;

      if (originalText.toLowerCase().includes(kw)) {
        console.log("🎯 MATCH:", kw, "in:", originalText.substring(0, 50));

        // For SVG text/tspan elements, we can't use innerHTML, so we style them directly
        if (elem.tagName === 'text' || elem.tagName === 'tspan' || elem.tagName === 'TEXT' || elem.tagName === 'TSPAN') {
          // SVG element - apply style attributes directly
          elem.setAttribute('data-pa-original-fill', elem.getAttribute('fill') || '');
          elem.setAttribute('data-pa-original-font-weight', elem.getAttribute('font-weight') || '');
          elem.setAttribute('data-pa-highlighted', 'true');
          elem.setAttribute('fill', '#000000');
          elem.setAttribute('font-weight', 'bold');

          // Add a highlight rect behind the text
          try {
            var bbox = elem.getBBox();
            var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('class', 'pa-highlight-rect');
            rect.setAttribute('x', bbox.x - 2);
            rect.setAttribute('y', bbox.y - 2);
            rect.setAttribute('width', bbox.width + 4);
            rect.setAttribute('height', bbox.height + 4);
            rect.setAttribute('fill', '#FFD700');
            rect.setAttribute('fill-opacity', '0.5');
            rect.setAttribute('rx', '2');
            elem.parentNode.insertBefore(rect, elem);
            highlightedCount++;
          } catch (e) {
            console.log("PA: bbox error:", e.message);
          }
        } else {
          // HTML element - use innerHTML replacement
          if (elem.querySelector && elem.querySelector('.pa-highlight-mark')) return;

          var newHTML = elem.innerHTML;
          var escapedKw = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          var regex = new RegExp('(' + escapedKw + ')', 'gi');
          var updated = newHTML.replace(regex, '<span class="pa-highlight-mark">$1</span>');

          if (updated !== newHTML) {
            try {
              elem.innerHTML = updated;
              console.log("✨ HIGHLIGHTED:", kw);
              highlightedCount++;
            } catch (e) {
              console.error("PA highlight error:", e);
            }
          }
        }
      }
    });
  });

  console.log("✅ Total highlighted:", highlightedCount);
  return highlightedCount > 0;
}

function clearHighlights() {
  console.log("🧹 Clearing highlights");

  // Clear HTML highlights
  document.querySelectorAll('.pa-highlight-mark').forEach(function (elem) {
    var text = elem.textContent;
    var parent = elem.parentNode;
    if (parent) {
      parent.replaceChild(document.createTextNode(text), elem);
      parent.normalize();
    }
  });

  // Clear SVG highlights
  document.querySelectorAll('.pa-highlight-rect').forEach(function (rect) {
    rect.remove();
  });

  // Restore SVG text original styles
  document.querySelectorAll('[data-pa-highlighted="true"]').forEach(function (elem) {
    var origFill = elem.getAttribute('data-pa-original-fill');
    var origWeight = elem.getAttribute('data-pa-original-font-weight');
    if (origFill) elem.setAttribute('fill', origFill);
    else elem.removeAttribute('fill');
    if (origWeight) elem.setAttribute('font-weight', origWeight);
    else elem.removeAttribute('font-weight');
    elem.removeAttribute('data-pa-highlighted');
    elem.removeAttribute('data-pa-original-fill');
    elem.removeAttribute('data-pa-original-font-weight');
  });

  // Also clear inside presentmode iframe
  try {
    var presentIframe = document.querySelector('iframe.punch-present-iframe');
    if (presentIframe) {
      var iDoc = presentIframe.contentDocument || presentIframe.contentWindow.document;
      if (iDoc) {
        iDoc.querySelectorAll('.pa-highlight-mark').forEach(function (elem) {
          var text = elem.textContent;
          var parent = elem.parentNode;
          if (parent) { parent.replaceChild(document.createTextNode(text), elem); parent.normalize(); }
        });
        iDoc.querySelectorAll('.pa-highlight-rect').forEach(function (r) { r.remove(); });
        iDoc.querySelectorAll('[data-pa-highlighted="true"]').forEach(function (elem) {
          var origFill = elem.getAttribute('data-pa-original-fill');
          var origWeight = elem.getAttribute('data-pa-original-font-weight');
          if (origFill) elem.setAttribute('fill', origFill);
          else elem.removeAttribute('fill');
          if (origWeight) elem.setAttribute('font-weight', origWeight);
          else elem.removeAttribute('font-weight');
          elem.removeAttribute('data-pa-highlighted');
          elem.removeAttribute('data-pa-original-fill');
          elem.removeAttribute('data-pa-original-font-weight');
        });
      }
    }
  } catch (e) { /* cross-origin */ }
}

// ===================== ACTION HANDLER =====================

function applyAction(intent, targetSlide, keywords) {
  if (intent === "next_slide") {
    // Simulate right arrow key press
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", keyCode: 39, bubbles: true, cancelable: true }));
    setStatus("→ Next slide");
  } else if (intent === "previous_slide") {
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", keyCode: 37, bubbles: true, cancelable: true }));
    setStatus("← Previous slide");
  } else if ((intent === "highlight" || intent === "speech") && keywords && keywords.length > 0) {
    var highlighted = highlightKeywords(keywords);
    setStatus(highlighted ? "✨ " + keywords.length + " keywords highlighted" : "⚠ No matches on slide");
  }
}

// ===================== BACKEND COMMUNICATION =====================

function sendToBackend(transcript) {
  setStatus("⚙️ Processing...");
  fetch("http://127.0.0.1:5000/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ speech: transcript, slide_text: "" })
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      console.log("📋 BACKEND DATA:", data);

      // Show keyword pills in toolbar
      var kwContainer = document.getElementById("pa-kw-container");
      if (kwContainer) {
        if (data.keywords && data.keywords.length > 0) {
          kwContainer.innerHTML = data.keywords.slice(0, 4).map(function (k) {
            return '<span class="pa-kw-pill">' + k + '</span>';
          }).join("");
        } else {
          kwContainer.innerHTML = "";
        }
      }

      setStatus("✓ " + new Date().toLocaleTimeString());

      // Highlight & apply actions
      if (data.keywords && data.keywords.length > 0) {
        setTimeout(function () {
          applyAction(data.intent, data.target_slide, data.keywords);
        }, 100);
      } else {
        applyAction(data.intent, data.target_slide, []);
      }
    })
    .catch(function (error) {
      console.error("❌ ERROR:", error);
      setStatus("❌ Backend error");
    });
}

// ===================== SLIDESHOW MODE SUPPORT =====================
// Watch for slideshow mode and re-inject the toolbar if needed
var slideshowObserver = new MutationObserver(function (mutations) {
  // Check if we entered slideshow/present mode
  var presentIframe = document.querySelector('iframe.punch-present-iframe');
  if (presentIframe && !document.getElementById("pa-toolbar")) {
    document.body.appendChild(toolbar);
  }

  // Also inject our highlight style into the present iframe
  if (presentIframe) {
    try {
      var iDoc = presentIframe.contentDocument || presentIframe.contentWindow.document;
      if (iDoc && !iDoc.getElementById("pa-style-iframe")) {
        var iStyle = document.createElement("style");
        iStyle.id = "pa-style-iframe";
        iStyle.textContent = `.pa-highlight-mark {
          background-color: #FFD700 !important;
          color: #000 !important;
          font-weight: bold !important;
          border-radius: 2px !important;
          box-shadow: 0 0 6px rgba(255, 215, 0, 0.6) !important;
          padding: 0 2px !important;
        }`;
        iDoc.head.appendChild(iStyle);
      }
    } catch (e) { /* cross-origin */ }
  }
});

slideshowObserver.observe(document.body, { childList: true, subtree: true });

console.log("✅ PA Ready - Compact Toolbar!");