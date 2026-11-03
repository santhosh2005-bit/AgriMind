import React, { useState } from 'react';
import {
  GitCommit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Eye,
  CloudSun,
  BookOpen,
  FileSpreadsheet,
  BrainCircuit,
  ShieldCheck,
  RotateCcw,
  Languages,
  Cpu,
  ChevronDown,
  ChevronUp,
  Info,
  Sparkles,
  Zap,
} from 'lucide-react';
import type { ExecutionPlan, PlanStep, StepStatus, TaskType } from '../types/api';

interface AgentMindmapViewProps {
  plan: ExecutionPlan | null;
  stepStatuses?: Record<string, StepStatus>;
  activeStepId?: string;
  onSelectStep?: (step: PlanStep) => void;
  title?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export const AgentMindmapView: React.FC<AgentMindmapViewProps> = ({
  plan,
  stepStatuses,
  activeStepId,
  onSelectStep,
  title = 'Agentic Execution Mindmap & Step DAG',
  collapsible = false,
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [selectedStep, setSelectedStep] = useState<PlanStep | null>(null);
  const [viewMode, setViewMode] = useState<'mindmap' | 'pipeline'>('mindmap');

  if (!plan || !plan.steps || plan.steps.length === 0) {
    return null;
  }

  const getTaskIcon = (taskType: TaskType) => {
    switch (taskType) {
      case 'vision_analysis':
        return <Eye className="w-4 h-4 text-emerald-400" />;
      case 'weather_retrieval':
        return <CloudSun className="w-4 h-4 text-sky-400" />;
      case 'knowledge_retrieval':
        return <BookOpen className="w-4 h-4 text-purple-400" />;
      case 'structured_data_query':
      case 'document_extraction':
        return <FileSpreadsheet className="w-4 h-4 text-amber-400" />;
      case 'agricultural_reasoning':
      case 'result_synthesis':
      case 'general_reasoning':
        return <BrainCircuit className="w-4 h-4 text-indigo-400" />;
      case 'verification':
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      case 'recovery':
        return <RotateCcw className="w-4 h-4 text-rose-400" />;
      case 'translation':
        return <Languages className="w-4 h-4 text-teal-400" />;
      default:
        return <Cpu className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStepStatus = (step: PlanStep): StepStatus => {
    return stepStatuses?.[step.step_id] || step.status || 'completed';
  };

  const getStatusBadge = (status: StepStatus) => {
    switch (status) {
      case 'completed':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Completed</span>
          </span>
        );
      case 'in_progress':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded-full border border-sky-500/30 animate-pulse">
            <Clock className="w-3 h-3 text-sky-400 animate-spin" />
            <span>Active</span>
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/30">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
            Pending
          </span>
        );
    }
  };

  // Group steps into stages for mindmap/dag visualization
  const toolSteps = plan.steps.filter((s) =>
    ['vision_analysis', 'weather_retrieval', 'knowledge_retrieval', 'structured_data_query', 'document_extraction', 'web_search'].includes(s.task_type)
  );
  const reasoningSteps = plan.steps.filter((s) =>
    ['agricultural_reasoning', 'result_synthesis', 'general_reasoning', 'calculation', 'code_analysis', 'summarization', 'translation'].includes(s.task_type)
  );
  const verificationSteps = plan.steps.filter((s) =>
    ['verification', 'recovery'].includes(s.task_type)
  );

  const handleNodeClick = (step: PlanStep) => {
    setSelectedStep(step);
    if (onSelectStep) {
      onSelectStep(step);
    }
  };

  return (
    <div className="glass-panel-glow rounded-2xl p-5 border border-emerald-500/30 shadow-2xl space-y-4 overflow-hidden relative">
      {/* Header with expand/collapse and view mode toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
            <GitCommit className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>{title}</span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {plan.steps.length} Steps
              </span>
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Interactive visualization of parallel tool execution, multi-model routing, and critic verification
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800 text-[11px]">
            <button
              type="button"
              onClick={() => setViewMode('mindmap')}
              className={`px-2.5 py-1 rounded-md font-semibold transition ${
                viewMode === 'mindmap'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Mindmap Flow
            </button>
            <button
              type="button"
              onClick={() => setViewMode('pipeline')}
              className={`px-2.5 py-1 rounded-md font-semibold transition ${
                viewMode === 'pipeline'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Pipeline List
            </button>
          </div>

          {collapsible && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title={isExpanded ? 'Collapse Mindmap' : 'Expand Mindmap'}
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          {/* Mindmap Flowchart Visualization Mode */}
          {viewMode === 'mindmap' ? (
            <div className="space-y-4 bg-slate-950/70 p-4 rounded-xl border border-slate-800/80">
              {/* Level 0: Input Root Node */}
              <div className="flex justify-center">
                <div className="w-full max-w-md p-3 rounded-xl bg-gradient-to-r from-slate-900 to-emerald-950/40 border border-emerald-500/40 shadow-lg text-center relative">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      User Inquiry & Multimodal Inputs
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 line-clamp-1 italic">
                    "{plan.rationale || 'Multimodal inquiry with image, documents & meteorological telemetry'}"
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center justify-center gap-1.5 text-[10px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      Crop: {plan.crop_identified || 'Solanaceae'}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/30">
                      DAG Plan: {plan.plan_id.slice(0, 8)}
                    </span>
                  </div>

                  {/* Connecting Arrow Down */}
                  <div className="absolute -bottom-3.5 left-1/2 -translate-x-1/2 w-0.5 h-3.5 bg-emerald-500/50" />
                </div>
              </div>

              {/* Connecting Splitter Bar */}
              <div className="flex justify-center pt-1 pb-1">
                <div className="w-3/4 max-w-xl h-0.5 bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
              </div>

              {/* Level 1: Parallel Evidence & Tool Retrieval Nodes */}
              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2 flex items-center justify-center gap-1.5">
                  <Zap className="w-3 h-3 text-emerald-400" />
                  <span>Stage 1: Parallel Multimodal & Telemetry Extraction</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(toolSteps.length > 0 ? toolSteps : plan.steps.slice(0, 3)).map((step) => {
                    const status = getStepStatus(step);
                    const isSelected = selectedStep?.step_id === step.step_id;
                    return (
                      <div
                        key={step.step_id}
                        onClick={() => handleNodeClick(step)}
                        className={`cursor-pointer p-3 rounded-xl border transition-all duration-300 flex flex-col justify-between gap-2 relative group hover:scale-[1.02] ${
                          isSelected
                            ? 'bg-emerald-950/40 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
                            : 'bg-slate-900/90 border-slate-800 hover:border-emerald-500/40'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-emerald-400 shrink-0">
                              {step.step_number}
                            </span>
                            <div className="p-1 rounded-md bg-slate-800/80">
                              {getTaskIcon(step.task_type)}
                            </div>
                            <span className="text-xs font-bold text-white group-hover:text-emerald-300 transition line-clamp-1">
                              {step.title}
                            </span>
                          </div>
                          {getStatusBadge(status)}
                        </div>

                        <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                          {step.description}
                        </p>

                        <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-[10px]">
                          <span className="text-slate-400 font-mono">
                            {step.assigned_model_id || 'Deterministic Tool'}
                          </span>
                          {step.actual_latency_ms && (
                            <span className="text-emerald-400 font-mono font-semibold">
                              {step.actual_latency_ms}ms
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Connecting Joiner Bar */}
              <div className="flex justify-center pt-2 pb-1">
                <div className="w-3/4 max-w-xl h-0.5 bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
              </div>

              {/* Level 2: Synthesis & Differential Reasoning Node */}
              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2 flex items-center justify-center gap-1.5">
                  <BrainCircuit className="w-3 h-3 text-indigo-400" />
                  <span>Stage 2: Multimodal Agronomic Differential Reasoning</span>
                </div>

                <div className="flex justify-center">
                  {(reasoningSteps.length > 0 ? reasoningSteps : plan.steps.slice(2, 4)).map((step) => {
                    const status = getStepStatus(step);
                    const isSelected = selectedStep?.step_id === step.step_id;
                    return (
                      <div
                        key={step.step_id}
                        onClick={() => handleNodeClick(step)}
                        className={`w-full max-w-xl cursor-pointer p-3.5 rounded-xl border transition-all duration-300 relative group hover:scale-[1.01] ${
                          isSelected
                            ? 'bg-indigo-950/40 border-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.25)]'
                            : 'bg-slate-900/90 border-slate-800 hover:border-indigo-500/40'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-[10px] font-bold text-indigo-300 shrink-0">
                              {step.step_number}
                            </span>
                            <BrainCircuit className="w-4 h-4 text-indigo-400" />
                            <span className="text-xs font-bold text-white group-hover:text-indigo-300 transition">
                              {step.title}
                            </span>
                          </div>
                          {getStatusBadge(status)}
                        </div>

                        <p className="text-[11px] text-slate-300 leading-relaxed">
                          {step.description}
                        </p>

                        <div className="flex items-center justify-between gap-2 pt-2 mt-2 border-t border-slate-800/80 text-[10px]">
                          <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-mono">
                            Model: {step.assigned_model_id || 'Gemini 2.5 Flash'}
                          </span>
                          {step.actual_latency_ms && (
                            <span className="text-indigo-300 font-mono">
                              Latency: {step.actual_latency_ms}ms
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Connecting Down Arrow to Verification */}
              <div className="flex justify-center pt-2 pb-1">
                <div className="w-1/2 max-w-md h-0.5 bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
              </div>

              {/* Level 3: Critic Verification & Final Output Node */}
              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2 flex items-center justify-center gap-1.5">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  <span>Stage 3: Critic Verification & Final Advisory Formulation</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl mx-auto">
                  {/* Verification Step */}
                  {(verificationSteps.length > 0 ? verificationSteps : plan.steps.slice(-2, -1)).map((step) => {
                    const status = getStepStatus(step);
                    const isSelected = selectedStep?.step_id === step.step_id;
                    return (
                      <div
                        key={step.step_id}
                        onClick={() => handleNodeClick(step)}
                        className={`cursor-pointer p-3 rounded-xl border transition-all duration-300 flex flex-col justify-between gap-1.5 ${
                          isSelected
                            ? 'bg-emerald-950/40 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
                            : 'bg-slate-900/90 border-slate-800 hover:border-emerald-500/40'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                            <span className="text-xs font-bold text-white line-clamp-1">
                              {step.title}
                            </span>
                          </div>
                          {getStatusBadge(status)}
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-2">
                          {step.description}
                        </p>
                        <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/60">
                          Critic Model: {step.assigned_model_id || 'Groq Qwen 27B / Critic Node'}
                        </div>
                      </div>
                    );
                  })}

                  {/* Final Advisory Terminal Node */}
                  <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-950/30 to-slate-900 border border-emerald-500/40 flex flex-col justify-between gap-1.5 shadow-lg">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-bold text-emerald-300">
                          Final Synthesized Advisory
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                        Ready
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300">
                      Delivered in requested language with empirical facts, hypotheses, interventions & follow-ups.
                    </p>
                    <div className="text-[10px] text-emerald-400 font-mono pt-1 border-t border-slate-800/60">
                      Target Lang: Multi-lingual (Tamil / English)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Pipeline List View Mode */
            <div className="space-y-2.5">
              {plan.steps.map((step) => {
                const status = getStepStatus(step);
                const isActive = activeStepId === step.step_id;
                const isSelected = selectedStep?.step_id === step.step_id;

                return (
                  <div
                    key={step.step_id}
                    onClick={() => handleNodeClick(step)}
                    className={`cursor-pointer p-3 rounded-xl border transition-all flex flex-wrap items-center justify-between gap-3 ${
                      isSelected
                        ? 'bg-emerald-950/30 border-emerald-400 shadow-md'
                        : isActive
                        ? 'bg-slate-900 border-sky-500/50'
                        : 'bg-slate-900/80 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-emerald-400 shrink-0">
                        {step.step_number}
                      </span>
                      <div className="p-1.5 rounded-lg bg-slate-800">
                        {getTaskIcon(step.task_type)}
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-white">{step.title}</h4>
                        <p className="text-[11px] text-slate-400 line-clamp-1">{step.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {step.assigned_model_id && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {step.assigned_model_id}
                        </span>
                      )}
                      {step.actual_latency_ms && (
                        <span className="text-[10px] font-mono text-emerald-400">
                          {step.actual_latency_ms}ms
                        </span>
                      )}
                      {getStatusBadge(status)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Interactive Selected Node Inspector Drawer */}
          {selectedStep && (
            <div className="p-3.5 rounded-xl bg-slate-900/95 border border-emerald-500/30 text-xs space-y-2 animate-in fade-in duration-200">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="font-bold text-white">
                    Step {selectedStep.step_number}: {selectedStep.title}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedStep(null)}
                  className="text-slate-400 hover:text-white text-[11px]"
                >
                  Close
                </button>
              </div>
              <p className="text-slate-300 leading-relaxed">{selectedStep.description}</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px] text-slate-400">
                <div>
                  <span className="text-slate-500">Task Type:</span>{' '}
                  <span className="font-mono text-slate-200">{selectedStep.task_type}</span>
                </div>
                <div>
                  <span className="text-slate-500">Assigned Model:</span>{' '}
                  <span className="font-mono text-emerald-400">{selectedStep.assigned_model_id || 'Deterministic Engine'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Latency:</span>{' '}
                  <span className="font-mono text-slate-200">{selectedStep.actual_latency_ms ? `${selectedStep.actual_latency_ms}ms` : 'Recorded'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Status:</span>{' '}
                  <span className="font-semibold text-emerald-400">{getStepStatus(selectedStep)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
