# AgriMind Setup and Developer Guide

This guide describes how to configure and run the AgriMind prototype on a local development machine.

---

## 1. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Python 3.11+ (recommended).
- **Node.js**: Node v18+ (for frontend dashboard).
- **Tesseract OCR (Optional)**: For optical character recognition of scanned PDFs/images.

---

## 2. Environment Configuration

1. Clone or navigate to the repository root:
   ```bash
   cd c:\AgriMind
   ```

2. Copy the template environment file:
   ```bash
   cp .env.example .env
   ```

3. Configure your API keys in `.env`:
   - `GEMINI_API_KEY`: Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).
   - `GROQ_API_KEY`: Groq API key from [Groq Console](https://console.groq.com/).
   - `OLLAMA_BASE_URL`: Local Ollama instance (default: `http://localhost:11434`).
   - *Note*: If API keys are not provided during development, AgriMind includes transparent mock adapters so you can develop and test without paid services.

---

## 3. Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run initial schema and unit tests:
   ```bash
   python -m unittest discover -s backend/tests -p "test_*.py"
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

---

## 4. Frontend Setup (Phase 9)

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Open your browser at `http://localhost:5173`.

---

## 5. Directory Structure Overview

```
AgriMind/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes and endpoints
│   │   ├── core/         # Settings, security, configuration
│   │   ├── schemas/      # Core Pydantic V2 schemas
│   │   ├── agents/       # LangGraph state & workflow nodes
│   │   ├── routing/      # Capability-aware model router
│   │   ├── models/       # Model registry & provider adapters
│   │   ├── tools/        # Weather, knowledge retrieval & data tools
│   │   ├── retrieval/    # PyMuPDF & FAISS vector search
│   │   ├── processing/   # Image, PDF, and CSV/JSON parsers
│   │   ├── verification/ # Deterministic checks & critic
│   │   ├── database/     # SQLite tables & session management
│   │   └── services/     # Orchestrator coordinator
│   └── tests/            # Pytest / Unittest test suite
├── frontend/             # React + Vite + Tailwind CSS dashboard
├── data/
│   ├── knowledge/        # Advisory PDFs and vector store
│   ├── sample_inputs/    # Example images, documents, CSVs
│   └── evaluation/       # Benchmark queries and evaluation records
├── docs/                 # Architecture, setup, API & evaluation docs
└── scripts/              # Ingestion and benchmark runner scripts
```
