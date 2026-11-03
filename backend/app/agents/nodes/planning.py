"""Node 3: Dynamic Planning Node formulating conditional execution DAG."""

import logging
from typing import List
from uuid import uuid4

from backend.app.schemas.enums import InputModality, TaskType, StepStatus, DomainCategory
from backend.app.schemas.plan import ExecutionPlan, PlanStep
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.node.planning")


def planning_node(state: AgriMindState) -> AgriMindState:
    """
    Formulates a conditional execution plan (DAG) based on the user's inquiry,
    provided modalities, domain classification, and extracted intent.
    Ensures non-relevant nodes are never scheduled and general-purpose queries
    receive tailored reasoning and verification pipelines.
    """
    logger.info("Executing Dynamic Planning Node")
    steps: List[PlanStep] = []
    step_num = 1
    gathering_dependencies: List[str] = []

    has_image = InputModality.IMAGE in state.detected_modalities
    has_pdf = InputModality.PDF in state.detected_modalities
    has_csv = (InputModality.CSV in state.detected_modalities) or (InputModality.JSON in state.detected_modalities)
    has_weather = state.request_understanding.get("has_weather_intent", False)
    needs_web_search = state.request_understanding.get("needs_web_search", False)

    domain_str = state.request_understanding.get("domain_category", DomainCategory.AGRICULTURE.value)
    try:
        domain = DomainCategory(domain_str)
    except ValueError:
        domain = DomainCategory.AGRICULTURE

    crop = state.request_understanding.get("primary_crop", "crop")

    # 1. Multimodal Branch: Visual Analysis (Only if image attached)
    vision_step_id = None
    if has_image:
        vision_step_id = f"step-vision-{uuid4().hex[:6]}"
        is_agri = domain == DomainCategory.AGRICULTURE
        v_title = f"Visual Foliar Inspection ({crop})" if is_agri else "Visual Multimodal Inspection"
        v_desc = (
            f"Inspect uploaded crop photograph for foliar chlorosis, curling, necrosis, or pest signs."
            if is_agri
            else "Analyze uploaded visual image content, extract key features, text, or visual patterns."
        )
        steps.append(
            PlanStep(
                step_id=vision_step_id,
                step_number=step_num,
                title=v_title,
                description=v_desc,
                task_type=TaskType.VISION_ANALYSIS,
                required_modalities=[InputModality.IMAGE, InputModality.TEXT],
                dependencies=[],
            )
        )
        gathering_dependencies.append(vision_step_id)
        step_num += 1

    # 2. Multimodal Branch: Document Extraction (Only if PDF attached)
    if has_pdf:
        pdf_step_id = f"step-pdf-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=pdf_step_id,
                step_number=step_num,
                title="Document Extraction & Parsing",
                description="Extract guidance text, tables, and section boundaries from user-supplied PDF documents.",
                task_type=TaskType.DOCUMENT_EXTRACTION,
                required_modalities=[InputModality.PDF],
                dependencies=[],
            )
        )
        gathering_dependencies.append(pdf_step_id)
        step_num += 1

    # 3. Multimodal Branch: Structured Data Query (Only if CSV/JSON attached)
    if has_csv:
        csv_step_id = f"step-csv-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=csv_step_id,
                step_number=step_num,
                title="Structured Tabular Data Query",
                description="Query parameters, statistics, and records from user-supplied CSV or JSON tabular data.",
                task_type=TaskType.STRUCTURED_DATA_QUERY,
                required_modalities=[InputModality.CSV if InputModality.CSV in state.detected_modalities else InputModality.JSON],
                dependencies=[],
            )
        )
        gathering_dependencies.append(csv_step_id)
        step_num += 1

    # 4. Multimodal Branch: Weather Retrieval (If weather intent or location present)
    if has_weather:
        weather_step_id = f"step-weather-{uuid4().hex[:6]}"
        loc_desc = state.request.location.place_name if state.request.location and state.request.location.place_name else "specified coordinates"
        steps.append(
            PlanStep(
                step_id=weather_step_id,
                step_number=step_num,
                title=f"Weather Telemetry Retrieval ({loc_desc})",
                description="Fetch temperature, relative humidity, and precipitation telemetry via Open-Meteo tool.",
                task_type=TaskType.WEATHER_RETRIEVAL,
                required_modalities=[InputModality.TEXT],
                dependencies=[],
            )
        )
        gathering_dependencies.append(weather_step_id)
        step_num += 1

    # 5. External Web Search Tool (If research domain or query requests external/fresh info)
    if domain == DomainCategory.RESEARCH or needs_web_search:
        search_step_id = f"step-search-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=search_step_id,
                step_number=step_num,
                title=f"Live Web Search & External Intelligence",
                description="Query public knowledge and verified external sources with URL source citations.",
                task_type=TaskType.WEB_SEARCH,
                required_modalities=[InputModality.TEXT],
                dependencies=[],
            )
        )
        gathering_dependencies.append(search_step_id)
        step_num += 1

    # 6. Domain-Specific Execution & Reasoning
    core_reason_id = None

    if domain == DomainCategory.MATHEMATICS:
        core_reason_id = f"step-math-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="Mathematical Reasoning & Deterministic Computation",
                description="Formulate step-by-step algebraic or arithmetic derivation and evaluate numerical precision.",
                task_type=TaskType.CALCULATION,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    elif domain == DomainCategory.CODING:
        core_reason_id = f"step-code-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="Code Analysis, Architecture & Generation",
                description="Analyze specifications, design robust algorithms, provide typed implementations and edge-case handling.",
                task_type=TaskType.CODE_ANALYSIS,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    elif domain == DomainCategory.TRANSLATION:
        core_reason_id = f"step-trans-{uuid4().hex[:6]}"
        target_lang = state.request_understanding.get("target_language", "target language")
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title=f"Multilingual Translation & Localization ({target_lang})",
                description="Translate input text faithfully while strictly preserving code blocks, numbers, formulas, and units.",
                task_type=TaskType.TRANSLATION,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    elif domain == DomainCategory.SUMMARIZATION:
        core_reason_id = f"step-summ-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="Executive Summarization & Key Insights",
                description="Distill complex information into concise, structured key takeaways and actionable conclusions.",
                task_type=TaskType.SUMMARIZATION,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    elif domain == DomainCategory.RESEARCH:
        core_reason_id = f"step-research-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="Research Synthesis & Evidence Grounding",
                description="Synthesize findings across retrieved external sources with verified citations and objective analysis.",
                task_type=TaskType.GENERAL_REASONING,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    elif domain == DomainCategory.GENERAL_KNOWLEDGE:
        core_reason_id = f"step-reason-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="General Knowledge Reasoning & Explanation",
                description="Provide comprehensive, structured explanation and analytical breakdown of the subject.",
                task_type=TaskType.GENERAL_REASONING,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    else:
        # Default: Agricultural domain
        rag_step_id = f"step-rag-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=rag_step_id,
                step_number=step_num,
                title=f"Agronomic Guidelines Retrieval ({crop})",
                description=f"Query FAISS index for relevant ICAR bulletins and extension manuals on {crop} disorders.",
                task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                required_modalities=[InputModality.TEXT],
                dependencies=[],
            )
        )
        gathering_dependencies.append(rag_step_id)
        step_num += 1

        core_reason_id = f"step-agri-reason-{uuid4().hex[:6]}"
        steps.append(
            PlanStep(
                step_id=core_reason_id,
                step_number=step_num,
                title="Agronomic Synthesis and Differential Diagnosis",
                description="Correlate symptoms, weather telemetry, and advisory evidence to produce plausible causes and recommendations.",
                task_type=TaskType.AGRICULTURAL_REASONING,
                required_modalities=[InputModality.TEXT],
                dependencies=list(gathering_dependencies),
            )
        )
        step_num += 1

    # 7. Core Verification & Critic Step (Validates findings, language consistency, math, evidence)
    verif_step_id = f"step-verif-{uuid4().hex[:6]}"
    steps.append(
        PlanStep(
            step_id=verif_step_id,
            step_number=step_num,
            title="Verification, Language Fidelity & Logic Check",
            description="Validate numerical calculations with Python, check evidence grounding, and verify output schema.",
            task_type=TaskType.VERIFICATION,
            required_modalities=[InputModality.TEXT],
            dependencies=[core_reason_id] if core_reason_id else list(gathering_dependencies),
        )
    )

    rationale = (
        f"Generated {len(steps)}-step dynamic DAG for domain '{domain.value}'. Branches activated: "
        f"Vision={has_image}, DocumentExtraction={has_pdf}, StructuredData={has_csv}, "
        f"WeatherRetrieval={has_weather}, WebSearch={(domain == DomainCategory.RESEARCH or needs_web_search)}."
    )

    state.execution_plan = ExecutionPlan(
        request_id=state.request.request_id,
        steps=steps,
        rationale=rationale,
        execution_budget_seconds=state.execution_budget_seconds,
    )

    # Initialize status map
    for s in steps:
        state.step_statuses[s.step_id] = StepStatus.PENDING

    logger.info(f"Planning complete: {len(steps)} steps planned. Rationale: {rationale}")
    return state
