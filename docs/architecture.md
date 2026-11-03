# AgriMind Architecture Specification

## 1. Executive Summary

**AgriMind** is a reusable, multimodal, multi-model agentic AI application designed for agricultural diagnostics, evidence retrieval, and decision support. 

Rather than relying on a single monolithic model or naively broadcasting identical prompts across multiple models, AgriMind implements **genuine agentic orchestration**:
- Translates unstructured farmer inquiries and multimodal inputs (crop photos, advisory PDFs, soil CSVs) into an explicit, validated execution plan (Directed Acyclic Graph).
- Selects and routes individual tasks to specialized models (commercial cloud and open-weight local) based on capability, latency, estimated cost, and historical reliability.
- Grounds factual reasoning in verified external tools (live weather telemetry, FAISS vector retrieval of agricultural advisories, and structured parcel records).
- Applies a dedicated verification stage that checks schema validity, validates deterministic calculations using native code, and flags unsupported claims.
- Records all routing decisions, model calls, tool executions, latencies, and fallback recovery events in SQLite for total observability.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 USER INTERFACE                                    |
|              React + TypeScript + Vite + Tailwind CSS Monitoring Dashboard        |
+-----------------------------------------------------------------------------------+
                                          |
                      REST / JSON / Multipart Form Data
                                          v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|   - CORS & Security Middleware    - Request Ingestion & Input Sanitation          |
|   - File Integrity / Limits       - Structured Pydantic Response Generation       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        LANGGRAPH ORCHESTRATION ENGINE                             |
|                                                                                   |
|  [Input Validator] -> [Request Understanding] -> [Dynamic Planner]                |
|                                                          |                        |
|                                          +---------------+                        |
|                                          v                                        |
|                                [Plan Step Validator]                             |
|                                          |                                        |
|                 +------------------------+------------------------+               |
|                 v                        v                        v               |
|      [Capability Router]        [Tool Connectors]     [Multimodal Processing]     |
|       - Task classification      - Weather (Open-Meteo)- PyMuPDF / OCR (PDFs)     |
|       - Modality matching        - Knowledge (FAISS)   - Pillow / OpenCV (Images) |
|       - Cost/Latency heuristic   - Structured Data     - Pandas (CSV / JSON)      |
|                 |                        |                        |               |
|                 +------------------------+------------------------+               |
|                                          |                                        |
|                                          v                                        |
|                              [Intermediate Validator]                             |
|                                          |                                        |
|                                          v                                        |
|                              [Agricultural Synthesizer]                           |
|                                          |                                        |
|                                          v                                        |
|                                [Verification & Critic]                            |
|                       - Deterministic calculation checks                          |
|                       - Source-evidence grounding checks                          |
|                       - Uncertainty & conflict labeling                           |
|                                          |                                        |
|                                          v                                        |
|                       [Fallback & Recovery Controller]                            |
|                       - Bounded retry / Fallback model switch                     |
|                                          |                                        |
|                                          v                                        |
|                              [Final Response Formatter]                           |
+-----------------------------------------------------------------------------------+
             |                                                  |
             v                                                  v
+-----------------------------+                    +--------------------------------+
|       MODEL REGISTRY        |                    |         PERSISTENCE            |
| - Gemini 1.5 Flash (Cloud)  |                    | SQLite / SQLAlchemy:           |
| - Groq Llama 3.3 70B (Cloud)|                    | - Sessions, Runs, Steps        |
| - Ollama Llama 3.2 3B(Local)|                    | - Model & Tool Calls, Latencies|
| - Mock Adapters (Dev/Test)  |                    | - Verification & Feedback logs |
+-----------------------------+                    +--------------------------------+
```

---

## 3. Core Architectural Pillars

### 3.1 Multimodal Input & Safe Ingestion
- Uploaded assets (images, documents, tabular files) are treated as **untrusted data**.
- Files undergo strict size, MIME-type, and SHA-256 integrity checks.
- Image processing extracts dimensional and color properties; PDF extraction isolates text per page; tabular files are parsed into validated structured dataframes.

### 3.2 Model Registry & Common Adapter Interface
- **Model Registry** decouples orchestration from specific model providers.
- Models are encapsulated behind a unified adapter interface (`generate()`, `supports_modality()`, `estimate_cost()`).
- The 3 model categories:
  1. **Commercial Model 1 (Multimodal / Vision)**: Google Gemini 1.5 Flash (cloud-hosted, fast multimodal reasoning).
  2. **Commercial Model 2 (High-throughput Reasoning / Synthesis)**: Groq-hosted Llama 3.3 70B Versatile (ultra-low latency, complex planning and structured synthesis).
  3. **Open-Weight Local Model (Edge / Privacy / Simple tasks)**: Ollama running Llama 3.2 3B or Mistral 7B locally (zero cost, offline availability, classification).

### 3.3 Capability-Aware Model & Tool Router
The router scores candidate models using an explicit, logged heuristic:
$$\text{Score}(M) = w_{\text{cap}} \cdot C_{\text{match}} + w_{\text{lat}} \cdot S_{\text{latency}} + w_{\text{cost}} \cdot S_{\text{cost}} - P_{\text{fail}}$$
- **Rule 1**: Modality constraint is absolute. If a step requires image processing, only models registered with vision capabilities are eligible.
- **Rule 2**: Real-world telemetry (weather, advisory guidelines) routes directly to deterministic tools rather than hallucinating models.
- **Rule 3**: Pre-designated fallback routes exist for every step. If the primary model times out or rate-limits, the step switches to the fallback model.

### 3.4 Explicit LangGraph Workflow State
The shared workflow state maintains:
- `user_request`: Sanitized input text, uploaded metadata, location.
- `execution_plan`: Sequence of planned steps, dependencies, and execution statuses.
- `intermediate_results`: Key-value store of outputs produced by completed steps.
- `retrieved_evidence`: Extracted citations from FAISS and tool APIs.
- `routing_decisions`: Recorded rationales for every model assignment.
- `verification_result`: Status of deterministic and evidentiary checks.
- `recovery_events`: History of retries, timeouts, and fallback switches.
- `final_response`: Validated structured response.

### 3.5 Dedicated Verification & Critic Stage
- **Deterministic Verification**: Calculations (e.g. soil N-P-K nutrient balancing, temperature thresholds) are recomputed in pure Python code.
- **Evidentiary Grounding**: Factual claims in the synthesis must link to IDs in `retrieved_evidence`.
- **Honest Uncertainty**: Sypmtoms are never diagnosed with absolute certainty from visual data alone. The system explicitly outputs `possible_causes` and `uncertainties_and_limitations`.

### 3.6 Persistence & Telemetry
Every run writes to SQLite:
- `execution_runs`, `execution_steps`, `model_calls`, `tool_calls`, `verification_results`, `recovery_events`.
- Measures real latency, token usage, and calculates costs using provider rate cards.
