import React, { useEffect, useState } from 'react';
import { X, Search, ArrowRight, RefreshCw } from 'lucide-react';
import type { ExecutionRunSummary } from '../types/api';
import { fetchRunHistory, fetchExecutionTrace } from '../services/api';

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRun: (trace: any) => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  onSelectRun,
}) => {
  const [runs, setRuns] = useState<ExecutionRunSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [cropFilter, setCropFilter] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchRunHistory(30, 0, cropFilter || undefined);
      setRuns(data.runs || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen, cropFilter]);

  if (!isOpen) return null;

  const handleSelectRun = async (runId: string) => {
    try {
      const fullTrace = await fetchExecutionTrace(runId);
      onSelectRun(fullTrace);
      onClose();
    } catch (err: any) {
      setError(`Failed to load trace: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-4xl max-h-[85vh] rounded-2xl border border-slate-800 shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-slate-800 bg-slate-900/50">
          <div>
            <h3 className="text-base font-bold text-white">Execution Run History</h3>
            <p className="text-xs text-slate-400">
              Auditable run telemetry stored in local SQLite database
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter bar */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/30 flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              placeholder="Filter by crop (e.g. tomato, wheat)..."
              className="w-full rounded-xl bg-slate-900 border border-slate-800 pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <button
            onClick={loadHistory}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition"
            title="Refresh runs"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Runs Table */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          ) : runs.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              {isLoading ? 'Loading historical executions...' : 'No runs found in database.'}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Crop</th>
                    <th className="py-2.5 px-3">Query</th>
                    <th className="py-2.5 px-3">Latency</th>
                    <th className="py-2.5 px-3">Cost</th>
                    <th className="py-2.5 px-3">Verification</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] text-slate-300">
                  {runs.map((r) => (
                    <tr key={r.run_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 text-slate-400">
                        {r.created_at ? new Date(r.created_at).toLocaleTimeString() : 'Recent'}
                      </td>
                      <td className="py-2.5 px-3 text-emerald-400 font-sans font-semibold">
                        {r.crop || 'Inquiry'}
                      </td>
                      <td className="py-2.5 px-3 font-sans truncate max-w-[200px]" title={r.query_text}>
                        {r.query_text}
                      </td>
                      <td className="py-2.5 px-3">{r.total_latency_ms.toFixed(1)} ms</td>
                      <td className="py-2.5 px-3 text-emerald-400">${r.total_cost_usd.toFixed(6)}</td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          r.verification_status === 'passed'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/10 text-amber-400'
                        }`}>
                          {r.verification_status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-sans">
                        <button
                          onClick={() => handleSelectRun(r.run_id)}
                          className="px-2.5 py-1 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-300 font-semibold border border-emerald-500/30 transition text-[11px] inline-flex items-center gap-1"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
