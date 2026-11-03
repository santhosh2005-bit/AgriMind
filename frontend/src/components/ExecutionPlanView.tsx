import {
  GitCommit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Cpu,
  CloudSun,
  BookOpen,
  Eye,
  FileSpreadsheet,
  BrainCircuit,
  ShieldCheck,
  RotateCcw,
  Calculator,
  Code,
  Languages,
  FileText,
  Search,
} from 'lucide-react';
import type { ExecutionPlan, TaskType, StepStatus } from '../types/api';
import { AgentMindmapView } from './AgentMindmapView';

interface ExecutionPlanViewProps {
  plan: ExecutionPlan | null;
  stepStatuses?: Record<string, StepStatus>;
  activeStepId?: string;
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
      return <FileSpreadsheet className="w-4 h-4 text-amber-400" />;
    case 'agricultural_reasoning':
    case 'result_synthesis':
    case 'general_reasoning':
      return <BrainCircuit className="w-4 h-4 text-indigo-400" />;
    case 'calculation':
      return <Calculator className="w-4 h-4 text-emerald-300" />;
    case 'code_analysis':
      return <Code className="w-4 h-4 text-cyan-400" />;
    case 'translation':
      return <Languages className="w-4 h-4 text-teal-400" />;
    case 'summarization':
      return <FileText className="w-4 h-4 text-orange-400" />;
    case 'web_search':
      return <Search className="w-4 h-4 text-blue-400" />;
    case 'verification':
      return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
    case 'recovery':
      return <RotateCcw className="w-4 h-4 text-rose-400" />;
    default:
      return <Cpu className="w-4 h-4 text-slate-400" />;
  }
};

const getStatusBadge = (status: StepStatus) => {
  switch (status) {
    case 'completed':
      return (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3" /> Completed
        </span>
      );
    case 'in_progress':
      return (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded-full border border-sky-500/30 animate-pulse">
          <Clock className="w-3 h-3 animate-spin" /> In Progress
        </span>
      );
    case 'failed':
      return (
        <span className="flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/30">
          <AlertTriangle className="w-3 h-3" /> Failed
        </span>
      );
    default:
      return (
        <span className="flex items-center gap-1 text-[10px] font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
          Pending
        </span>
      );
  }
};

export const ExecutionPlanView: React.FC<ExecutionPlanViewProps> = ({
  plan,
  stepStatuses,
  activeStepId,
}) => {
  if (!plan) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 text-center text-slate-500 text-sm">
        No execution plan formulated yet. Enter a query to formulate an agentic DAG plan.
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-200">
            Formulated Directed Acyclic Graph (DAG) Plan
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400">Identified Crop:</span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-semibold border border-emerald-500/20">
            {plan.crop_identified || 'General Inquiry'}
          </span>
          <span className="text-slate-400 ml-2">Total Steps:</span>
          <span className="font-bold text-slate-200">{plan.steps.length}</span>
        </div>
      </div>

      {/* Rationale explanation */}
      {plan.rationale && (
        <p className="text-xs text-slate-400 mb-4 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
          <span className="text-emerald-400 font-semibold">Plan Rationale:</span> {plan.rationale}
        </p>
      )}

      {/* Visual Step-by-Step Mindmap Diagram */}
      <div className="mb-6">
        <AgentMindmapView
          plan={plan}
          stepStatuses={stepStatuses}
          activeStepId={activeStepId}
          title="Interactive Step-by-Step Execution Mindmap"
          defaultExpanded={true}
        />
      </div>

      <div className="flex items-center gap-2 mb-3 text-xs font-bold text-slate-300 uppercase tracking-wider">
        <GitCommit className="w-4 h-4 text-emerald-400" />
        <span>Sequential Execution Step Details</span>
      </div>

      {/* Steps Pipeline */}
      <div className="space-y-3">
        {plan.steps.map((step) => {
          const currentStatus = stepStatuses?.[step.step_id] || step.status;
          const isActive = activeStepId === step.step_id;

          return (
            <div
              key={step.step_id}
              className={`p-3.5 rounded-xl border transition-all ${
                isActive
                  ? 'bg-emerald-950/20 border-emerald-500/50 shadow-[0_0_15px_rgba(34,197,94,0.15)]'
                  : currentStatus === 'completed'
                  ? 'bg-slate-900/90 border-slate-800/80'
                  : 'bg-slate-900/50 border-slate-800/50 opacity-80'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-300">
                    {step.step_number}
                  </span>
                  <div className="p-1.5 rounded-lg bg-slate-800/80">
                    {getTaskIcon(step.task_type)}
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">
                      {step.title}
                    </h4>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Task: {step.task_type}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {step.assigned_model_id && (
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-emerald-300">
                      {step.assigned_model_id}
                    </span>
                  )}
                  {getStatusBadge(currentStatus)}
                </div>
              </div>

              {/* Metrics & Dependencies bar */}
              <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/50 mt-2">
                <div>
                  {step.dependencies.length > 0 ? (
                    <span>Depends on: {step.dependencies.join(', ')}</span>
                  ) : (
                    <span className="text-slate-500">No prerequisites (Root node)</span>
                  )}
                </div>

                <div className="flex items-center gap-3 font-mono">
                  {step.actual_latency_ms != null && typeof step.actual_latency_ms === 'number' && (
                    <span>{step.actual_latency_ms.toFixed(1)} ms</span>
                  )}
                  {step.actual_cost_usd != null && typeof step.actual_cost_usd === 'number' && (
                    <span className="text-emerald-400">
                      ${step.actual_cost_usd.toFixed(6)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
