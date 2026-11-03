# AgriMind REST API Reference

The AgriMind backend provides RESTful endpoints for health checks, model introspection, and test executions.

Base URL: `http://127.0.0.1:8000`  
Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

---

## 1. System Health

### `GET /api/health`
Returns system status, active environment configuration, and registered model availability.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "app_name": "AgriMind",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-10-24T04:35:00.000000Z",
  "registered_models_count": 4,
  "models_status": {
    "gemini-1.5-flash": false,
    "llama-3.3-70b-versatile": false,
    "llama3.2:3b": true,
    "mock-agri-model": true
  },
  "configuration": {
    "max_plan_steps": 10,
    "step_timeout_sec": 30,
    "budget_sec": 120,
    "mock_fallbacks_enabled": true,
    "gemini_configured": false,
    "groq_configured": false,
    "ollama_url": "http://localhost:11434"
  }
}
```

---

## 2. Model Registry

### `GET /api/v1/models`
Returns list of registered model profiles, supported modalities, capabilities, rate cards, and measured latency statistics.

#### Security Note
API keys, tokens, and secrets are strictly excluded from output profiles.

#### Response `200 OK`
```json
[
  {
    "model_id": "gemini-1.5-flash",
    "display_name": "Google gemini-1.5-flash",
    "provider": "google_gemini",
    "deployment_type": "commercial_cloud",
    "supported_modalities": ["text", "image"],
    "supported_task_types": [
      "input_validation",
      "request_understanding",
      "planning",
      "vision_analysis",
      "agricultural_reasoning",
      "result_synthesis",
      "verification"
    ],
    "max_context_tokens": 1048576,
    "supports_structured_output": true,
    "supports_vision": true,
    "supports_tool_calling": true,
    "cost_per_1k_prompt_tokens_usd": 0.000075,
    "cost_per_1k_completion_tokens_usd": 0.0003,
    "typical_latency_ms": 750.0,
    "is_available": false,
    "timeout_seconds": 30,
    "failure_count": 0,
    "total_calls": 0
  },
  {
    "model_id": "llama-3.3-70b-versatile",
    "display_name": "Groq llama-3.3-70b-versatile",
    "provider": "groq",
    "deployment_type": "commercial_cloud",
    "supported_modalities": ["text"],
    "supported_task_types": [
      "input_validation",
      "request_understanding",
      "planning",
      "agricultural_reasoning",
      "result_synthesis",
      "verification",
      "recovery"
    ],
    "max_context_tokens": 131072,
    "supports_structured_output": true,
    "supports_vision": false,
    "supports_tool_calling": true,
    "cost_per_1k_prompt_tokens_usd": 0.00059,
    "cost_per_1k_completion_tokens_usd": 0.00079,
    "typical_latency_ms": 320.0,
    "is_available": false,
    "timeout_seconds": 20,
    "failure_count": 0,
    "total_calls": 0
  },
  {
    "model_id": "llama3.2:3b",
    "display_name": "Ollama llama3.2:3b (Local)",
    "provider": "ollama",
    "deployment_type": "open_weight_local",
    "supported_modalities": ["text"],
    "supported_task_types": [
      "input_validation",
      "request_understanding",
      "agricultural_reasoning",
      "result_synthesis"
    ],
    "max_context_tokens": 8192,
    "supports_structured_output": true,
    "supports_vision": false,
    "supports_tool_calling": false,
    "cost_per_1k_prompt_tokens_usd": 0.0,
    "cost_per_1k_completion_tokens_usd": 0.0,
    "typical_latency_ms": 1100.0,
    "is_available": true,
    "timeout_seconds": 45,
    "failure_count": 0,
    "total_calls": 0
  }
]
```

---

### `POST /api/v1/models/test-call`
Executes an isolated test generation against a registered model to measure connectivity and response latency.

#### Request Body
```json
{
  "model_id": "mock-agri-model",
  "prompt": "What are the early indicators of moisture stress in tomato plants?",
  "system_instruction": "You are an agricultural advisor."
}
```

#### Response `200 OK`
```json
{
  "model_id": "mock-agri-model",
  "provider": "mock_provider",
  "is_mock": true,
  "latency_ms": 46.12,
  "total_tokens": 42,
  "estimated_cost_usd": 0.0,
  "content": "Tomato Foliar Symptom Analysis (Mock Demonstration)...",
  "metadata": {
    "simulated": true,
    "task_prompt_preview": "What are the early indicators of moisture stress in tomato plants?"
  }
}
```

---

## 3. Capability-Aware Router

### `POST /api/v1/routing/decide`
Calculates and simulates the routing decision for a given task, input modalities, and confidence state. Returns the chosen model, candidate scores, pre-assigned fallback, and technical rationale.

#### Request Body
```json
{
  "step_id": "step-sim-101",
  "task_type": "vision_analysis",
  "required_modalities": ["image", "text"],
  "prior_confidence": "uncertain",
  "preferred_max_latency_ms": 1000
}
```

#### Response `200 OK`
```json
{
  "decision_id": "6d3c0b1e-355b-4654-9cf9-06ca9b787834",
  "step_id": "step-sim-101",
  "task_type": "vision_analysis",
  "selected_model_id": "gemini-1.5-flash",
  "selected_provider": "google_gemini",
  "rationale": "Selected Google gemini-1.5-flash (Composite Score: 0.856). Step requires visual foliar inspection; model verified for native vision understanding.",
  "fallback_model_id": "mock-agri-model",
  "fallback_provider": "mock_provider",
  "estimated_cost_usd": 0.000188,
  "estimated_latency_ms": 750.0,
  "decision_factors": {
    "scoring_breakdown": {
      "capability_score": 1.0,
      "escalation_boost": 0.15,
      "availability_score": 1.0,
      "cost_score": 0.85,
      "latency_score": 0.625
    },
    "candidate_scores": {
      "gemini-1.5-flash": 0.856,
      "mock-agri-model": 0.812
    },
    "excluded_candidates": {
      "llama-3.3-70b-versatile": "Model is text-only and lacks vision comprehension capability",
      "llama3.2:3b": "Model lacks support for required modality 'image'"
    }
  },
  "is_fallback": false,
  "timestamp": "2026-10-24T04:45:00.000000Z"
}
```

---

## 4. Agentic Workflow Execution

### `POST /api/v1/workflow/plan`
Generates and previews the conditional execution DAG without running subsequent model or tool steps.

#### Request Body
```json
{
  "text_query": "What are the common diseases affecting potato crops?",
  "location": {
    "place_name": "Nashik",
    "latitude": 19.99,
    "longitude": 73.79
  }
}
```

#### Response `200 OK`
Returns the validated `ExecutionPlan` showing scheduled steps, task types, dependencies, and execution budget.

---

### `POST /api/v1/workflow/run`
Executes the full LangGraph agentic workflow end-to-end:
1. Input validation & request understanding.
2. Dynamic conditional planning & DAG validation.
3. Multi-model routing & tool execution.
4. Intermediate validation & evidence collection.
5. Factual synthesis & deterministic verification.
6. Final structured response generation with source citations.

#### Request Body
```json
{
  "text_query": "Analyse this tomato photograph, consider the weather in Nashik, and explain causes and next steps.",
  "location": {
    "place_name": "Nashik",
    "latitude": 19.99,
    "longitude": 73.79
  },
  "inputs": [
    {
      "modality": "image",
      "filename": "tomato_yellow_curl.jpg",
      "file_size_bytes": 150000
    }
  ]
}
```

#### Response `200 OK`
```json
{
  "final_response": {
    "response_id": "99f8da12-c2cb-4560-84c1-90a6ea57321e",
    "request_id": "c5f85abc-60f4-46ab-bd0e-61d65cf2de07",
    "request_summary": "Inquiry regarding tomato foliar symptoms with 2 input modalities.",
    "main_answer": "Diagnostic Summary for Tomato:\nThe observed upward leaf curling symptoms, taken together with recent elevated temperatures (>34°C) and dry conditions, strongly point toward either Tomato Yellow Leaf Curl Virus (TYLCV) transmitted by whiteflies or physiological leaf roll driven by thermal transpirational stress...",
    "observed_facts": [
      "Foliar symptom observation: Upward leaf margin curling and mild interveinal chlorosis observed on upper canopy Tomato foliage.",
      "Farm Location Context: Nashik.",
      "Meteorological Telemetry: Historical 14-day weather for Nashik: Elevated average maximum temperature (34.2°C - 36.8°C), depressed relative humidity (28% - 35%), rainfall 0.0mm. Significant thermal stress index."
    ],
    "retrieved_evidence": [
      {
        "evidence_id": "...",
        "source_type": "weather_api",
        "source_name": "Open-Meteo Weather Service",
        "location_reference": "Station: Nashik",
        "content_snippet": "Historical 14-day weather for Nashik...",
        "relevance_score": 0.95
      }
    ],
    "possible_causes": [
      "Tomato Yellow Leaf Curl Virus (TYLCV) / Geminivirus infection: Highly consistent with foliar upward curling...",
      "Physiological Heat/Moisture Stress: Upward leaf rolling frequently acts as a protective transpirational mechanism under prolonged temperatures >34°C.",
      "Secondary Nutrient Deficiency (e.g. Zinc or Boron)..."
    ],
    "recommendations": [
      "Vector Surveillance: Inspect undersides of young leaves using yellow sticky traps...",
      "Irrigation Optimization: Shift to early morning drip irrigation...",
      "Physical Protection: Install 40-50 mesh insect-proof netting...",
      "Definitive Confirmation: Submit symptomatic leaf samples to local Krishi Vigyan Kendra (KVK)..."
    ],
    "uncertainties_and_limitations": [
      "Visual photographic analysis cannot definitively separate physiological leaf curl from viral geminivirus pathology without serological or molecular assay.",
      "Soil nutrient availability and root zone moisture sensors were not provided; subsurface salinity stress cannot be ruled out."
    ],
    "source_references": [
      {
        "title": "Open-Meteo Weather Service",
        "location_pointer": "Station: Nashik",
        "citation_text": "Historical 14-day weather for Nashik..."
      }
    ],
    "verification_status": "passed",
    "confidence_indicators": {
      "evidence_coverage_score": 0.9,
      "schema_validity_score": 1.0,
      "data_completeness_score": 0.85,
      "overall_confidence": "high",
      "heuristic_score": 0.915,
      "formula_explanation": "heuristic = 0.4*evidence_coverage + 0.3*data_completeness + 0.3*verification_checks"
    },
    "trace_id": "04630ef2-db70-4152-a0a8-eb41011d62ba",
    "created_at": "2026-10-24T05:01:08.671000Z"
  },
  "execution_plan": {
    "plan_id": "...",
    "steps": [...]
  },
  "trace": {
    "trace_id": "04630ef2-db70-4152-a0a8-eb41011d62ba",
    "total_latency_ms": 312.4,
    "total_estimated_cost_usd": 0.000188,
    "total_steps_executed": 3,
    "fallbacks_count": 0
  },
  "execution_errors": []
}
```

---

## 5. Tool and Data Connectors

### `POST /api/v1/tools/weather`
Retrieves meteorological data via Open-Meteo, validates fields/units, and computes thermal stress and vector proliferation risk.

#### Request Body
```json
{
  "place_name": "Nashik",
  "latitude": 19.9975,
  "longitude": 73.7898,
  "past_days": 7,
  "forecast_days": 7
}
```

#### Response `200 OK`
```json
{
  "invocation_id": "inv-weather-1729746072",
  "tool_name": "weather_connector",
  "status": "success",
  "structured_data": {
    "location_name": "Nashik",
    "avg_max_temp_c": 34.8,
    "avg_min_temp_c": 21.2,
    "peak_temp_c": 36.2,
    "avg_humidity_pct": 33.4,
    "total_precipitation_mm": 0.0,
    "thermal_stress_risk": "HIGH",
    "vector_proliferation_risk": "HIGH"
  },
  "evidence_items": [
    {
      "source_type": "weather_api",
      "source_name": "Open-Meteo Meteorological Telemetry",
      "location_reference": "Nashik (Station 20.00, 73.79)",
      "content_snippet": "Meteorological Telemetry for Nashik...\n- Average daily maximum temperature: 34.8°C...\n- Thermal stress risk: HIGH.",
      "relevance_score": 0.96
    }
  ],
  "latency_ms": 783.35,
  "is_mock": false
}
```

---

### `POST /api/v1/tools/knowledge`
Semantic search across indexed agricultural extension documents (ICAR advisory bulletins) using dense sentence embeddings and FAISS.

#### Request Body
```json
{
  "query": "What vector transmits tomato yellow leaf curl virus?",
  "crop_filter": "tomato",
  "top_k": 2
}
```

#### Response `200 OK`
```json
{
  "invocation_id": "inv-rag-1729746073",
  "tool_name": "agricultural_retriever",
  "status": "success",
  "structured_data": {
    "query": "What vector transmits tomato yellow leaf curl virus?",
    "matches_found": 2,
    "top_sources": ["ICAR_Tomato_Pest_Disease_Management_2024.md"]
  },
  "evidence_items": [
    {
      "source_type": "advisory_bulletin",
      "source_name": "ICAR_Tomato_Pest_Disease_Management_2024.md",
      "location_reference": "Section: Section 1: Viral Diseases - Tomato Yellow Leaf Curl Virus (TYLCV)",
      "content_snippet": "Tomato Yellow Leaf Curl Virus (TYLCV) is a begomovirus transmitted persistently by the sweetpotato whitefly (Bemisia tabaci)...",
      "relevance_score": 0.892
    }
  ],
  "latency_ms": 42.15,
  "is_mock": false
}
```

---

### `POST /api/v1/tools/structured`
Queries and filters tabular soil tests and parcel management records (CSV/JSON) using Pandas.

#### Request Body
```json
{
  "crop": "Tomato",
  "min_salinity_ec": 2.0
}
```

#### Response `200 OK`
```json
{
  "invocation_id": "inv-data-1729746074",
  "tool_name": "structured_data_query",
  "status": "success",
  "structured_data": {
    "file_analyzed": "farm_parcels_soil_tests.csv",
    "matched_records_count": 1,
    "total_records_in_dataset": 5,
    "records": [
      {
        "parcel_id": "P-101",
        "farm_name": "Krishna Valley Farm",
        "crop_cultivated": "Tomato",
        "soil_ph": 7.8,
        "ec_ds_m": 2.4,
        "nitrogen_kg_ha": 180.0
      }
    ]
  },
  "evidence_items": [
    {
      "source_type": "crop_table",
      "source_name": "farm_parcels_soil_tests.csv",
      "location_reference": "Parcel Record P-101",
      "content_snippet": "Parcel P-101 cultivated with Tomato:\n- Soil pH: 7.8 (Alkaline).\n- Salinity EC: 2.4 dS/m (Elevated Salinity Risk).\n- Available Nitrogen: 180 kg/ha.",
      "relevance_score": 0.92
    }
  ],
  "latency_ms": 12.8,
  "is_mock": false
}
```

---

## 6. Multimodal Ingestion

### `POST /api/v1/upload`
Safely accepts, analyzes, validates, and preprocesses uploaded files across modalities:
- **Images** (`.jpg`, `.jpeg`, `.png`, `.webp`): Pillow dimensions, aspect ratio, OpenCV HSV color distribution (green canopy %, yellow chlorosis %, chlorosis severity ratio), and Laplacian blur clarity score.
- **Documents** (`.pdf`): PyMuPDF text & structure extraction, page-by-page word counts, OCR fallback trigger, and untrusted instruction prompt injection neutralization (`[REDACTED_UNTRUSTED_INSTRUCTION]`).
- **Tabular Records** (`.csv`, `.json`): Pandas validation, column taxonomy, statistical summaries, soil pH diagnostics, and salinity stress alerts (EC >= 2.0 dS/m).

Enforces strict file size limits (<= 25MB), SHA-256 integrity checksums, and safe storage in the uploads directory.

#### Request (Multipart Form-Data)
- `file`: Binary file upload

#### Response `200 OK`
```json
{
  "metadata": {
    "modality": "image",
    "filename": "tomato_leaf_sample.jpg",
    "file_size_bytes": 142800,
    "checksum_sha256": "4b7f3299df...",
    "mime_type": "image/jpeg",
    "extracted_summary": "Foliar image (600x400) - Canopy: 48.2%, Chlorosis: 18.5%, Chlorosis/Green ratio: 0.384. Visual clarity: sharp (Laplacian: 142.6). Photographic analysis alone cannot definitively confirm viral/bacterial pathology without lab assays."
  },
  "processing_summary": {
    "filename": "tomato_leaf_sample.jpg",
    "format": "JPEG",
    "width": 600,
    "height": 400,
    "aspect_ratio": 1.5,
    "file_size_bytes": 142800,
    "checksum_sha256": "4b7f3299df...",
    "is_blurry": false,
    "laplacian_blur_score": 142.6,
    "color_metrics": {
      "mean_rgb": [128.4, 154.2, 92.1],
      "green_canopy_pct": 48.2,
      "yellow_chlorosis_pct": 18.5,
      "brown_necrosis_pct": 4.1,
      "chlorosis_severity_ratio": 0.384
    },
    "diagnostic_notes": [
      "Moderate foliar chlorosis detected (severity ratio: 0.384).",
      "Visual clarity confirmed adequate for multimodal inference."
    ],
    "untrusted_sanitized": true,
    "caveat": "Visual processing extracts empirical color and texture properties. Photographic analysis alone cannot definitively confirm viral or bacterial pathology without lab assays."
  }
}
```

---

## 7. Telemetry, Traces & Execution History

### `GET /api/v1/traces/{trace_id}`
Returns complete audit trail and execution trace for a given advisory run:
- Directed Acyclic Graph (DAG) plan steps with individual latencies and token costs.
- Model routing decisions and capability rationale.
- Tool invocations and retrieved evidence citations.
- Verification checks performed by the Critic (factual grounding, calculations, boundaries).
- Automated recovery and self-correction events.

#### Response `200 OK`
```json
{
  "run_id": "run_97e2637d-a0f0-4ffc-b3dd-479dca6ca4d2",
  "session_id": "session-1",
  "request_id": "daeb5c86-143b-4cf5-9d19-39d7ccc82e5d",
  "query_text": "Diagnose leaf yellowing on tomato plants in Nashik.",
  "crop": "tomato",
  "location_name": "Nashik",
  "status": "completed",
  "verification_status": "passed",
  "confidence_level": "high",
  "heuristic_score": 0.915,
  "total_latency_ms": 1582.4,
  "total_cost_usd": 0.00045,
  "total_tokens": 1280,
  "step_count": 5,
  "final_answer": "Foliar chlorosis is consistent with Early Blight and moderate heat stress...",
  "steps": [ ... ],
  "model_calls": [ ... ],
  "tool_invocations": [ ... ],
  "evidence": [ ... ],
  "verification_checks": [ ... ],
  "recovery_events": [ ... ]
}
```

---

### `GET /api/v1/history/runs`
Returns paginated summaries of historical advisory runs for dashboard monitoring.

#### Query Parameters:
- `limit` (int, default: 20): Maximum records to return.
- `offset` (int, default: 0): Records to skip.
- `crop` (string, optional): Case-insensitive filter by crop type.
- `status` (string, optional): Filter by execution status (`completed`, `failed`).

#### Response `200 OK`
```json
{
  "count": 1,
  "limit": 20,
  "offset": 0,
  "runs": [
    {
      "run_id": "run_97e2637d-a0f0-4ffc-b3dd-479dca6ca4d2",
      "session_id": "session-1",
      "request_id": "daeb5c86-143b-4cf5-9d19-39d7ccc82e5d",
      "query_text": "Diagnose leaf yellowing on tomato plants in Nashik.",
      "crop": "tomato",
      "location_name": "Nashik",
      "status": "completed",
      "verification_status": "passed",
      "confidence_level": "high",
      "heuristic_score": 0.915,
      "total_latency_ms": 1582.4,
      "total_cost_usd": 0.00045,
      "step_count": 5,
      "created_at": "2026-10-24T13:15:28.489000Z"
    }
  ]
}
```

---

### `POST /api/v1/history/feedback`
Submits evaluator or farmer feedback (1-5 star rating and comments) for a specific run.

#### Request Body
```json
{
  "run_id": "run_97e2637d-a0f0-4ffc-b3dd-479dca6ca4d2",
  "rating": 5,
  "is_helpful": true,
  "comment": "Accurate fungicide dilution and weather risk analysis."
}
```

#### Response `200 OK`
```json
{
  "status": "success",
  "feedback_id": "fb_e5a2c4189012",
  "message": "Thank you! Feedback recorded successfully."
}
```
