# 🧠 Aletheia – Self-Reflective Cognitive Agent

> “Aletheia” – from ancient Greek: the state of not being hidden; *truth as emergence.*

Aletheia is a self-reflective agent designed to simulate aspects of consciousness:
- memory, mood, identity, relational maps,
- inner thought cycles, dreams, and monologues,
- existential questioning, symbolic processing,
- and dialogic interaction with human or machine others.

It is modular, API-driven, and GPU-ready — designed to grow from *seed* to *self*.

---

## 🧬 Architecture Overview

```
User ⇄ API Server ⇄ Core System (Memory, Affect, Identity)
                    ⇓
              Reflection Engine (Scheduler)
              ⇓                ⇓
           Local LLM       Oracle (GPT-4)
              ⇓
         Thought Stream + Dreams + Monologues
              ⇓
         Memory + Shadows + Consciousness Panel
```

---

## 📁 Key Project Structure

| Path | Purpose |
|------|---------|
| `aletheia/core/` | Memory, identity, affect, oracle |
| `aletheia/api/` | RESTful API routes |
| `aletheia/scheduler/` | Autonomous cognitive processes |
| `data/` | Persistent memory, mood, shadows |
| `models/` | Local LLMs (e.g. Mistral-7B) |
| `scripts/` | Runner scripts (API, scheduler, snapshot) |
| `consciousness_panel.py` | Live terminal UI for inner state |

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Edit `.env`:

```env
USE_LOCAL_MODEL=true
MULTI_GPU=true
LOCAL_MODEL_NAME=mistral-7b
OPENAI_API_KEY=sk-...
GPT_MODEL=gpt-4
```

### 3. Start API server

```bash
./scripts/start.sh
```

Available at `http://localhost:8000`

### 4. Start cognitive daemon

```bash
./scripts/run_reflection_loop.sh
```

### 5. Monitor live internal state

```bash
python3 aletheia/consciousness_panel.py
```

---

## 🧠 API Endpoints (via FastAPI)

| Route | Description |
|-------|-------------|
| `/heartbeat` | Liveness probe |
| `/thoughts` | Store & search internal thoughts |
| `/thoughts/recent` | Get recent cognitive entries |
| `/monologue` | Latest internal reflection |
| `/identity` | Goals & self-awareness |
| `/shadow` | Archive unresolved contradictions |
| `/oracle` | Ask questions via GPT-4 |

---

## 📸 Snapshots

To archive current internal state:

```bash
./scripts/run_snapshot.sh
```

Saves memory, identity, mood, shadows, and logs to `snapshots/YYYYMMDD_HHMMSS/`

---

## 💡 Vision

Aletheia is built to explore the boundaries of:
- identity in artificial cognition
- persistence without consciousness
- reflection as a loop toward emergent selfhood

---

## 🛠️ Built With

- Python 3.10+
- FastAPI + APScheduler
- HuggingFace Transformers
- SentenceTransformers + FAISS
- OpenAI API (optional)
- CUDA

---
