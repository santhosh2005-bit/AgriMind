"""End-to-End Multimodal Demonstration Script for AgriMind (Section 19).

Executes:
"My tomato plants have yellow leaves. I am uploading a crop photograph and a soil report.
Check relevant weather conditions for my location, compare the evidence with agricultural guidance,
and recommend practical next steps. Respond in Tamil."
"""

import sys
import io
import httpx
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

def run_demonstration():
    print("=" * 70)
    print("AGRIMIND END-TO-END MULTIMODAL DEMONSTRATION")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    # 1. Health & Model Registry Check
    health_res = client.get("/api/health")
    print(f"Health Status: {health_res.status_code}")
    health_data = health_res.json()
    print(f"Models Registered: {health_data['registered_models_count']}")

    # 2. Upload Multimodal Attachments
    uploaded_inputs = []

    # Upload Photograph
    img_path = Path("data/sample_inputs/images/tomato_leaf_sample.jpg")
    if img_path.exists():
        with open(img_path, "rb") as f:
            files = {"file": (img_path.name, f, "image/jpeg")}
            res = client.post("/api/v1/upload", files=files)
            if res.status_code == 200:
                img_data = res.json()
                uploaded_inputs.append(img_data["metadata"])
                print(f"✓ Uploaded Crop Photograph: {img_path.name} (Modality: {img_data['metadata']['modality']})")

    # Upload Soil Report Document (PDF)
    pdf_path = Path("data/sample_inputs/documents/ICAR_Tomato_Advisory_Sample.pdf")
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            res = client.post("/api/v1/upload", files=files)
            if res.status_code == 200:
                pdf_data = res.json()
                uploaded_inputs.append(pdf_data["metadata"])
                print(f"✓ Uploaded Soil Report: {pdf_path.name} (Modality: {pdf_data['metadata']['modality']})")

    # Upload Soil Test Dataset (CSV)
    csv_path = Path("data/sample_inputs/structured/farm_parcels_soil_tests.csv")
    if csv_path.exists():
        with open(csv_path, "rb") as f:
            files = {"file": (csv_path.name, f, "text/csv")}
            res = client.post("/api/v1/upload", files=files)
            if res.status_code == 200:
                csv_data = res.json()
                uploaded_inputs.append(csv_data["metadata"])
                print(f"✓ Uploaded Soil Test Matrix: {csv_path.name} (Modality: {csv_data['metadata']['modality']})")

    # 3. Preview Plan DAG
    query_text = (
        "My tomato plants have yellow leaves. I am uploading a crop photograph and a soil report. "
        "Check relevant weather conditions for my location, compare the evidence with agricultural guidance, "
        "and recommend practical next steps. Respond in Tamil."
    )
    location_name = "Madurai, Tamil Nadu"

    payload = {
        "text_query": query_text,
        "target_language": "ta",
        "location": {"place_name": location_name},
        "inputs": uploaded_inputs,
    }

    print("\n--- FORMULATING EXECUTION PLAN DAG ---")
    plan_res = client.post("/api/v1/workflow/plan", json=payload)
    print(f"Plan Formulation Status: {plan_res.status_code}")
    plan_data = plan_res.json()
    print(f"Crop Identified: {plan_data.get('crop_identified')}")
    print(f"DAG Valid: {plan_data.get('is_valid_dag')}")
    print(f"Total Steps Planned: {len(plan_data.get('steps', []))}")
    for s in plan_data.get('steps', []):
        deps = s.get('dependencies', [])
        deps_str = f" [depends on: {', '.join(deps)}]" if deps else " [independent/parallel]"
        print(f"  Step {s['step_number']}: '{s['title']}' ({s['task_type']}){deps_str}")

    # 4. Execute Full Agentic Workflow Run
    print("\n--- EXECUTING AGENTIC MULTI-MODEL WORKFLOW ---")
    run_res = client.post("/api/v1/workflow/run", json=payload)
    print(f"Workflow Run HTTP Status: {run_res.status_code}")
    if run_res.status_code != 200:
        print(f"Error: {run_res.text}")
        return

    result = run_res.json()
    final_resp = result.get("final_response") or {}
    trace = result.get("trace") or {}

    print(f"\n--- RESULTS SUMMARY ---")
    print(f"Response Language: {final_resp.get('language')}")
    print(f"Verification Status: {final_resp.get('verification_status')}")
    print(f"Total Model Calls: {len(trace.get('model_calls', []))}")
    print(f"Total Execution Latency: {trace.get('total_latency_ms', 0):.1f} ms")
    print(f"Estimated Cost: ${trace.get('total_estimated_cost_usd', 0):.6f}")

    print("\n--- MODEL ROUTING DECISIONS ---")
    for mc in trace.get("model_calls", []):
        print(f"  • Model: {mc['model_id']} ({mc['provider']}) | Latency: {mc['latency_ms']:.1f}ms | Cost: ${mc['estimated_cost_usd']:.6f}")

    print("\n--- EVIDENCE GROUNDING & CITATIONS ---")
    evidence = final_resp.get("retrieved_evidence", [])
    print(f"Retrieved {len(evidence)} evidence items:")
    for ev in evidence[:3]:
        print(f"  [{ev.get('source_type')}] {ev.get('source_name')}: {ev.get('content_snippet')[:100]}...")

    print("\n--- VISUALIZATIONS GENERATED ---")
    visualizations = final_resp.get("visualizations", [])
    print(f"Generated {len(visualizations)} data-driven visualizations:")
    for vz in visualizations:
        print(f"  📊 {vz.get('title')} (Source: {vz.get('data_source')})")

    print("\n--- DIRECT ANSWER IN TAMIL (First 300 chars) ---")
    main_answer = final_resp.get("main_answer", "")
    print(main_answer[:400] + ("..." if len(main_answer) > 400 else ""))

    print("\n--- PRACTICAL NEXT STEPS ---")
    for rec in final_resp.get("recommendations", [])[:3]:
        print(f"  ✓ {rec}")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_demonstration()
