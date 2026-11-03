# 🌱 AgriMind: Reusable Multi-Model, Multimodal & Agentic AI System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.x-red.svg)](https://docs.pydantic.dev/)

Built for the **FarmwiseAI Campus Product Challenge**.

AgriMind is an agentic agricultural intelligence application that combines farmer observations (text questions, crop photographs, soil CSVs, advisory PDFs) with verified external evidence (real-time weather data, indexed agronomic guidance) through transparent multi-model routing and rigorous fact verification.

---

## 🎯 Key Architectural Features

1. **Genuine Agentic Orchestration**: Rather than naively querying multiple models with the same prompt, AgriMind constructs an explicit Directed Acyclic Graph (DAG) plan with conditional branching and execution budgets.
2. **Tri-Model Capability Routing**: Transparently routes steps across:
   - **Commercial Cloud Model 1**: Google Gemini 1.5 Flash (vision and multimodal analysis).
   - **Commercial Cloud Model 2**: Groq Llama 3.3 70B (fast complex planning and synthesis).
   - **Open-Weight Local Model**: Ollama Llama 3.2 3B (edge tasks, classification, zero cost).
3. **Deterministic Grounding & Tools**: 
   - Live weather telemetry via Open-Meteo API.
   - Grounded PDF knowledge retrieval with page-level citations using PyMuPDF and FAISS.
   - Structured parcel/soil data queries via Pandas.
4. **Independent Verification & Critic Stage**:
   - Re-verifies soil and thermal calculations in deterministic Python code.
   - Distinguishes observed symptoms, retrieved facts, possible explanations, and unverified assumptions.
   - Calibrated multidimensional confidence scoring.
5. **Observability & Fault Recovery**:
   - Complete execution trace persisted to SQLite (latencies, token counts, costs in USD, step statuses).
   - Graceful fallback paths for rate-limits, model timeouts, and schema errors.

---

## 🗺️ Implementation Roadmap

| Phase | Description | Status |
|:---|:---|:---:|
| **Phase 1** | Project structure, architecture docs, core Pydantic schemas, initial test suite | ✅ Completed |
| **Phase 2** | FastAPI backend, health checks, settings, model registry & common adapter interface | ✅ Completed |
| **Phase 3** | Three-model integration (Gemini, Groq, Ollama) & capability-aware router | ✅ Completed |
| **Phase 4** | LangGraph workflow, dynamic planner, shared state, and conditional DAG | ✅ Completed |
| **Phase 5** | Tool connectors: Open-Meteo Weather, FAISS Agricultural Retrieval, CSV querying | ✅ Completed |
| **Phase 6** | Multimodal input pipeline: PyMuPDF/OCR, Pillow/OpenCV image processing | ✅ Completed |
| **Phase 7** | Verification engine, deterministic calculation critic, confidence scoring, fallbacks | ✅ Completed |
| **Phase 8** | SQLite persistence, execution tracing, telemetry, and run history | ✅ Completed |
| **Phase 9** | React + Vite + Tailwind CSS monitoring and diagnostic dashboard | ✅ Completed |
| **Phase 10** | Repeatable evaluation suite, baseline vs proposed comparison, failure simulations | ✅ Completed |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Node.js v18+ (tested on Node v24)
- (Optional) Ollama running locally with `ollama run llama3.2:3b`

### 1. Backend Setup & Run
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

# Start FastAPI Server (runs at http://127.0.0.1:8000)
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup & Run
```powershell
# Open a new terminal in the frontend directory
cd frontend
npm install
npm run dev
# Dashboard launches at http://localhost:5173
```

### 3. Run Unit Test Suite (67 Tests)
```powershell
python -m unittest discover -s backend/tests -p "test_*.py"
```

### 4. Run Empirical Benchmark Suite
```powershell
python scripts/run_evaluations.py
# Generates data/evaluation/evaluation_results.json and docs/evaluation.md
```

---

## 📚 Documentation Links
- [System Architecture](file:///c:/AgriMind/docs/architecture.md)
- [Empirical Evaluation & Benchmark Report](file:///c:/AgriMind/docs/evaluation.md)
- [Requirements Traceability Matrix](file:///c:/AgriMind/docs/requirements_mapping.md)
- [REST API Specifications](file:///c:/AgriMind/docs/api.md)
- [Setup and Developer Guide](file:///c:/AgriMind/docs/setup.md)
