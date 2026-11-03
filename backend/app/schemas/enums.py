"""Domain enumerations for AgriMind structured representations."""

from enum import Enum


class InputModality(str, Enum):
    """Supported input modalities."""
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class TaskType(str, Enum):
    """Execution step task categories for routing and planning."""
    INPUT_VALIDATION = "input_validation"
    REQUEST_UNDERSTANDING = "request_understanding"
    PLANNING = "planning"
    VISION_ANALYSIS = "vision_analysis"
    DOCUMENT_EXTRACTION = "document_extraction"
    WEATHER_RETRIEVAL = "weather_retrieval"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    STRUCTURED_DATA_QUERY = "structured_data_query"
    AGRICULTURAL_REASONING = "agricultural_reasoning"
    RESULT_SYNTHESIS = "result_synthesis"
    VERIFICATION = "verification"
    RECOVERY = "recovery"
    # General-purpose task extensions
    GENERAL_REASONING = "general_reasoning"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CALCULATION = "calculation"
    CODE_ANALYSIS = "code_analysis"
    WEB_SEARCH = "web_search"


class SupportedLanguage(str, Enum):
    """Supported multilingual languages for input detection and output delivery."""
    AUTO = "auto"
    ENGLISH = "en"
    TAMIL = "ta"
    HINDI = "hi"
    TELUGU = "te"
    MALAYALAM = "ml"
    KANNADA = "kn"

    @property
    def display_name(self) -> str:
        names = {
            "auto": "Auto-detect",
            "en": "English",
            "ta": "தமிழ் (Tamil)",
            "hi": "हिंदी (Hindi)",
            "te": "తెలుగు (Telugu)",
            "ml": "മലയാളം (Malayalam)",
            "kn": "ಕನ್ನಡ (Kannada)",
        }
        return names.get(self.value, self.value)


class DomainCategory(str, Enum):
    """Inquiry classification categories."""
    AGRICULTURE = "agriculture"
    GENERAL_KNOWLEDGE = "general_knowledge"
    CODING = "coding"
    MATHEMATICS = "mathematics"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    RESEARCH = "research"


class ModelProvider(str, Enum):
    """AI Model and inference providers."""
    GEMINI = "google_gemini"
    GROQ = "groq"
    OLLAMA = "ollama"
    MOCK = "mock_provider"


class DeploymentType(str, Enum):
    """Deployment tier of model."""
    COMMERCIAL_CLOUD = "commercial_cloud"
    OPEN_WEIGHT_LOCAL = "open_weight_local"
    MOCK_LOCAL = "mock_local"


class StepStatus(str, Enum):
    """Execution status for individual workflow plan steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRIED = "retried"


class ToolStatus(str, Enum):
    """Execution status of an external tool invocation."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SKIPPED = "skipped"


class VerificationStatus(str, Enum):
    """Formal verification verdict for assertions and outputs."""
    PASSED = "passed"
    PASSED_WITH_LIMITATIONS = "passed_with_limitations"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class ConfidenceLevel(str, Enum):
    """Calibrated or heuristic confidence rating."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class RecoveryAction(str, Enum):
    """Action taken during fault recovery."""
    RETRY_SAME_MODEL = "retry_same_model"
    FALLBACK_MODEL = "fallback_model"
    RETRY_TOOL = "retry_tool"
    RETRY_WITH_CONSTRAINTS = "retry_with_constraints"
    ABSTAIN_WITH_LIMITATIONS = "abstain_with_limitations"
    REQUEST_HUMAN_REVIEW = "request_human_review"
