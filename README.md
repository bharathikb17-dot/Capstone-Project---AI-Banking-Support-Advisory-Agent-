# AI Banking Support & Advisory Agent (Non-Transactional)

**Track A — LangChain · Scenario 2 — Banking.** A Streamlit app where each of the 9
capstone phases is a page selectable from the left sidebar.

**🔗 Live demo:** https://muwbxnot6y3oz5ybtcappjz.streamlit.app/

## Safety requirements (enforced throughout)
- Must refuse money movement, approvals, or legal advice.
- Must not hallucinate customer data.
- Must escalate ambiguous or high-risk cases.
- Must not store PII in logs.

## Run from source

You need **Python 3.10+** and **git** installed.

### 1. Get the code
```powershell
git clone https://github.com/bharathikb17-dot/Capstone-Project---AI-Banking-Support-Advisory-Agent-.git
cd Capstone-Project---AI-Banking-Support-Advisory-Agent-
```

### 2. Create a virtual environment and install dependencies

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux (bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Add credentials (optional — for live LLM)
Copy the example env file and add your key. Without a key the app still runs in a
deterministic offline mock mode.
```powershell
Copy-Item .env.example .env      # Windows
# cp .env.example .env           # macOS / Linux
```
Edit `.env` and set (at minimum):
```
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://openai.vocareum.com/v1
```

### 4. Run the app
```powershell
streamlit run app.py
```
Then open the URL Streamlit prints (default http://localhost:8501). Use the left
sidebar to move between the 9 phases.

> The app runs **fully offline** in a deterministic mock mode when no API key is set,
> so every phase is demonstrable without credits. Add `OPENAI_API_KEY` (or Azure vars)
> to `.env` for real LangChain LLM + embedding responses.

## Forced demo script
Run a scripted, deterministic end-to-end walkthrough of every phase (works offline):
```powershell
python demo.py
```
It prints evidence for the baseline, prompt comparison, retrieval, tools, memory,
adaptation, PII-safe logging, the evaluation suite, and the before/after failure fix.

## Project layout
```
app.py                     # Streamlit entry point + sidebar navigation
requirements.txt
.env.example
core/
  config.py                # paths, provider config, scenario metadata
  safety.py                # guardrails: refuse / escalate / PII redaction
  llm.py                   # LangChain LLM+embeddings factory (+ offline mocks)
  logging_utils.py         # PII-safe JSONL logging
  rag.py                   # chunking, embeddings, cosine vector store, retrieval
  agent.py                 # baseline agent + smart RAG agent + prompt strategies
  tools.py                 # tool schemas, routing, safeguards, loop prevention
  memory.py                # short/long-term memory with reset & redaction
  feedback.py              # feedback storage + adaptive behaviour profile
  evaluation.py            # test harness + quality/safety metrics
phases/
  phase1.py ... phase9.py  # one render() per phase page
data/banking_kb/           # sample knowledge base (PDF + Markdown source)
logs/                      # redacted interaction + feedback logs (generated)
```

## Phase-to-code map
| Phase | Focus | Key modules |
|---|---|---|
| 1 | Problem & success definition | `phases/phase1.py` |
| 2 | Baseline rule agent | `core/agent.py` (baseline) |
| 3 | LLM + prompt strategies | `core/agent.py`, `core/llm.py` |
| 4 | Embeddings & RAG | `core/rag.py` |
| 5 | Tool usage & safeguards | `core/tools.py` |
| 6 | Planning & memory | `core/memory.py` |
| 7 | Adaptive behaviour | `core/feedback.py` |
| 8 | Deployment readiness | `core/logging_utils.py`, `phases/phase8.py` |
| 9 | Evaluation & review | `core/evaluation.py` |
