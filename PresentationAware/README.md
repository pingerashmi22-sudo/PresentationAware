# PresentationAware# PresentationAware

An AI-powered, voice-controlled presentation assistant. Speak naturally during your presentation — the system listens, understands your intent using an LLM, and automatically controls your slides in real time.

---

## How It Works

1. A microphone captures your speech after a wake word is detected
2. Audio is transcribed to text via OpenAI Whisper (STT)
3. The transcript is cleaned and sent to an LLM with slide context
4. The LLM returns a structured JSON intent (e.g. `go_to_slide`, `highlight`)
5. The intent is validated and executed — slides move, keywords highlight

---

## API Setup

### Prerequisites

- Python 3.10 or higher
- An [OpenAI API key](https://platform.openai.com/account/api-keys)
- A PowerPoint file loaded in the `slides/` directory

### Step 1 — Clone the repo
```bash
git clone https://github.com/pingerashmi22-sudo/PresentationAware.git
cd PresentationAware
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

This installs: `openai`, `python-dotenv`, `pydantic`, and all other required packages.

### Step 3 — Create your `.env` file

Inside the `member_1_speech/` folder, create a file named `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

> ⚠️ Never commit this file. It is already listed in `.gitignore`.

### Step 4 — Run the system
```bash
python main.py
```

Say the wake word, then speak a command like:
- *"Go to slide five"*
- *"Highlight scalability"*
- *"Next slide"*
- *"Go back"*

Say **"exit"** to shut down the system.

---

## Modular Architecture
```
PresentationAware/
│
├── main.py                        ← Entry point. Orchestrates the full pipeline loop.
│
├── member_1_speech/               ── AUDIO & WAKE WORD (Member 1 & 4)
│   ├── .env                       ← API keys (never committed)
│   ├── .gitignore                 ← Ignores .env, *.wav, __pycache__/
│   ├── controller.py              ← Emits "Transcription Ready" events to main.py
│   ├── 05_wake_word.py            ← Activates mic only after wake word is heard
│   ├── speech_engine.py           ← Sends clean text to ContextManager
│   └── 03_whisper_test.py         ← API-based Whisper STT transcription
│
├── speech/                        ── RAW SPEECH HANDLING (Member 2 & 4)
│   ├── speech_input.py            ← Low-level microphone stream management
│   └── speech_parser.py           ← Cleans transcript before sending to LLM
│
├── context/                       ── BRAIN & MEMORY (Member 1 & 2)
│   ├── llm_processor.py           ← [NEW] Calls OpenAI API, returns JSON intent
│   ├── prompts.py                 ← [NEW] System prompt + few-shot examples
│   ├── intent_validator.py        ← Validates LLM JSON via Pydantic schema
│   ├── context_manager.py         ← Tracks current slide + exposes LLM context
│   ├── history_manager.py         ← Rolling 30-second transcript memory
│   └── state.py                   ← Active session variables (kept as-is)
│
├── slide_mapper/                  ── SLIDE KNOWLEDGE BASE (Member 3)
│   ├── ppt_reader.py              ← Scrapes titles, bullets, and notes from PPT
│   ├── mapper.py                  ← Maps LLM "Target Topic" to physical Slide IDs
│   └── slide_data.py              ← Data models for slide objects (kept as-is)
│
├── slides/                        ── SLIDE EXECUTION ENGINE (Member 3 & 4)
│   ├── slide_index.json           ← Rich AI-readable summary of every slide
│   ├── slide_indexer.py           ← Auto-generates slide_index.json on PPT update
│   ├── content_extractor.py       ← Condenses slide text into LLM context strings
│   ├── chart_highlighter.py       ← Triggers animations via LLM "Action" field
│   ├── element_locator.py         ← Finds text coordinates for Smart Zooming
│   ├── ocr_reader.py              ← Backup text extractor for image-based slides
│   ├── ppt_loader.py              ← Indexes PPT at startup
│   └── slide_engine.py            ← Logic-to-PowerPoint visual bridge
│
└── utils/                         ── HARDWARE CONTROL (Member 4)
    ├── slide_controller.py        ← Absolute slide navigation (go_to_slide, next, prev)
    └── visual_highlighter.py      ← Dynamic highlight based on LLM-detected terms
```

### Data Flow
```
Microphone
    │
    ▼
speech_input.py       ← captures audio
    │
    ▼
03_whisper_test.py    ← transcribes audio → raw text string
    │
    ▼
speech_parser.py      ← cleans filler words → clean text string
    │
    ▼
context_manager.py    ← logs to history, builds LLM context dict
    │
    ▼
llm_processor.py      ← sends text + context to OpenAI → raw JSON dict
    │
    ▼
intent_validator.py   ← validates JSON schema → IntentSchema object
    │
    ▼
main.py               ← executes action (next_slide / highlight / go_to_slide …)
    │
    ▼
slide_controller.py / visual_highlighter.py  ← controls PowerPoint
```

---

## File Status Key

| Symbol | Meaning |
|--------|---------|
| `[NEW]` | Newly created file — did not exist before |
| *(kept as-is)* | Unchanged file — no modifications needed |
| *(no label)* | Existing file that has been modified |

---

## Team

| Member | Role | Key Files |
|--------|------|-----------|
| Member 1 | AI Logic Lead | `llm_processor.py`, `prompts.py`, `03_whisper_test.py` |
| Member 2 | Systems Integrator | `main.py`, `context_manager.py`, `history_manager.py`, `intent_validator.py`, `speech_parser.py`, `README.md` |
| Member 3 | Knowledge Engineer | `ppt_reader.py`, `slide_indexer.py`, `slide_index.json`, `content_extractor.py` |
| Member 4 | Execution & Audio Lead | `slide_controller.py`, `visual_highlighter.py`, `speech_engine.py`, `05_wake_word.py` |