import React from 'react';
import {
  Activity,
  DollarSign,
  Clock,
  Layers,
  TrendingUp,
} from 'lucide-react';
import type { ModelCallRecord } from '../types/api';

interface TelemetryTraceViewProps {
  totalLatencyMs?: number;
  totalCostUsd?: number;
  modelCalls?: ModelCallRecord[];
  stepCount?: number;
}

export const TelemetryTraceView: React.FC<TelemetryTraceViewProps> = ({
  totalLatencyMs = 0,
  totalCostUsd = 0,
  modelCalls = [],
  stepCount = 0,
}) => {
  const totalTokens = modelCalls.reduce((acc, m) => acc + (m.total_tokens || 0), 0);
  const promptTokens = modelCalls.reduce((acc, m) => acc + (m.prompt_tokens || 0), 0);
  const completionTokens = modelCalls.reduce((acc, m) => acc + (m.completion_tokens || 0), 0);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 pb-4 border-b border-slate-800">
        <Activity className="w-5 h-5 text-emerald-400" />
        <h3 className="text-sm font-bold text-slate-200">
          Telemetry & Multi-Model Inference Metrics
        </h3>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Latency */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span>Total Latency</span>
          </div>
          <p className="text-lg font-mono font-bold text-slate-100">
            {totalLatencyMs.toFixed(1)} <span className="text-xs font-normal text-slate-400">ms</span>
          </p>
        </div>

        {/* Cost */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            <span>Est. Cost (USD)</span>
          </div>
          <p className="text-lg font-mono font-bold text-emerald-400">
            ${totalCostUsd.toFixed(6)}
          </p>
        </div>

        {/* Tokens */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Tokens (P/C)</span>
          </div>
          <p className="text-lg font-mono font-bold text-purple-300">
            {totalTokens}{' '}
            <span className="text-[10px] font-normal text-slate-400">
              ({promptTokens}/{completionTokens})
            </span>
          </p>
        </div>

        {/* Steps */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>Steps Executed</span>
          </div>
          <p className="text-lg font-mono font-bold text-slate-100">
            {stepCount}{' '}
            <span className="text-xs font-normal text-slate-400">steps</span>
          </p>
        </div>
      </div>

      {/* Model Invocations Table */}
      {modelCalls.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Multi-Model Routing Audit ({modelCalls.length} calls)
          </span>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Step</th>
                  <th className="py-2.5 px-3">Routed Model</th>
                  <th className="py-2.5 px-3">Provider</th>
                  <th className="py-2.5 px-3">Tokens</th>
                  <th className="py-2.5 px-3">Latency</th>
                  <th className="py-2.5 px-3">Cost</th>
                  <th className="py-2.5 px-3">Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] text-slate-300">
                {modelCalls.map((call, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    <td className="py-2 px-3 text-slate-400">{call.step_id}</td>
                    <td className="py-2 px-3 text-emerald-400 font-semibold">{call.model_id}</td>
                    <td className="py-2 px-3 text-slate-400">{call.provider}</td>
                    <td className="py-2 px-3">{call.total_tokens}</td>
                    <td className="py-2 px-3">{call.latency_ms.toFixed(1)} ms</td>
                    <td className="py-2 px-3 text-emerald-400">${call.estimated_cost_usd.toFixed(6)}</td>
                    <td className="py-2 px-3">
                      {call.is_mock ? (
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 font-sans">
                          Offline Mock
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-sans">
                          Live API
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
