/** TypeScript definitions for AgriMind API and execution traces */

export type TaskType =
  | 'input_validation'
  | 'request_understanding'
  | 'planning'
  | 'vision_analysis'
  | 'document_extraction'
  | 'weather_retrieval'
  | 'knowledge_retrieval'
  | 'structured_data_query'
  | 'agricultural_reasoning'
  | 'result_synthesis'
  | 'verification'
  | 'recovery'
  | 'general_reasoning'
  | 'translation'
  | 'summarization'
  | 'calculation'
  | 'code_analysis'
  | 'web_search';

export type SupportedLanguage = 'auto' | 'en' | 'ta' | 'hi' | 'te' | 'ml' | 'kn';

export type StepStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'skipped'
  | 'retried';

export type VerificationStatus =
  | 'passed'
  | 'passed_with_limitations'
  | 'needs_review'
  | 'failed';

export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'uncertain';

export interface PlanStep {
  step_id: string;
  step_number: number;
  title: string;
  description?: string;
  task_type: TaskType;
  assigned_model_id?: string;
  status: StepStatus;
  dependencies: string[];
  actual_latency_ms?: number;
  actual_cost_usd?: number;
  error_message?: string;
}

export interface ExecutionPlan {
  plan_id: string;
  request_id: string;
  crop_identified?: string;
  rationale: string;
  steps: PlanStep[];
  is_valid_dag: boolean;
}

export interface RetrievedEvidence {
  evidence_id: string;
  source_type: string;
  source_name: string;
  location_reference?: string;
  content_snippet: string;
  relevance_score?: number;
  metadata?: Record<string, unknown>;
}

export interface VerificationCheck {
  check_id: string;
  check_type: string;
  status: VerificationStatus;
  target_claim?: string;
  details: string;
  deterministic_passed?: boolean;
}

export interface ConfidenceBreakdown {
  evidence_coverage_score: number;
  schema_validity_score: number;
  data_completeness_score: number;
  overall_confidence: ConfidenceLevel;
  heuristic_score: number;
  formula_explanation: string;
}

export interface VerificationResult {
  verification_id: string;
  overall_status: VerificationStatus;
  checks: VerificationCheck[];
  confidence: ConfidenceBreakdown;
  missing_information: string[];
  conflicts_detected: string[];
}

export interface RecoveryEvent {
  step_id: string;
  trigger_reason: string;
  action_taken: string;
  from_target?: string;
  to_target?: string;
  success: boolean;
  details: string;
}

export interface ModelCallRecord {
  step_id: string;
  model_id: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  is_mock: boolean;
  created_at?: string;
}

export interface VisualizationData {
  chart_type: 'weather_trend' | 'soil_metrics' | 'crop_comparison' | string;
  title: string;
  subtitle?: string;
  data_source: string;
  unit?: string;
  labels: string[];
  series: Array<{
    name: string;
    data: number[];
    color?: string;
  }>;
  notes?: string;
}

export interface FinalResponse {
  response_id: string;
  request_id: string;
  request_summary: string;
  main_answer: string;
  observed_facts: string[];
  retrieved_evidence: RetrievedEvidence[];
  possible_causes: string[];
  recommendations: string[];
  follow_up_questions?: string[];
  visualizations?: VisualizationData[];
  uncertainties_and_limitations: string[];
  verification_status: VerificationStatus;
  confidence_indicators: ConfidenceBreakdown;
  language?: string;
  trace_id: string;
  created_at: string;
}

export interface ExecutionRunSummary {
  run_id: string;
  session_id?: string;
  request_id: string;
  query_text: string;
  crop?: string;
  location_name?: string;
  status: string;
  verification_status: string;
  confidence_level: string;
  heuristic_score: number;
  total_latency_ms: number;
  total_cost_usd: number;
  step_count: number;
  created_at: string;
}

export interface ExecutionTraceView {
  run_id: string;
  session_id?: string;
  request_id: string;
  query_text: string;
  crop?: string;
  location_name?: string;
  status: string;
  verification_status: string;
  confidence_level: string;
  heuristic_score: number;
  total_latency_ms: number;
  total_cost_usd: number;
  total_tokens: number;
  step_count: number;
  final_answer?: string;
  created_at: string;
  completed_at?: string;
  steps: PlanStep[];
  model_calls: ModelCallRecord[];
  tool_invocations: Array<{
    step_id: string;
    tool_name: string;
    status: string;
    latency_ms: number;
    is_mock: boolean;
    parameters: Record<string, unknown>;
  }>;
  evidence: RetrievedEvidence[];
  verification_checks: VerificationCheck[];
  recovery_events: RecoveryEvent[];
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  registered_models_count: number;
  models_status: Record<string, boolean>;
  configuration: Record<string, unknown>;
}
