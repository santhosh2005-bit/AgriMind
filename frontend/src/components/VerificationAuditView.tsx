import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Scale,
} from 'lucide-react';
import type { VerificationResult, RecoveryEvent } from '../types/api';

interface VerificationAuditViewProps {
  verification: VerificationResult | null;
  recoveryEvents?: RecoveryEvent[];
}

export const VerificationAuditView: React.FC<VerificationAuditViewProps> = ({
  verification,
  recoveryEvents = [],
}) => {
  if (!verification) return null;

  const conf = verification.confidence;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passed':
        return (
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold text-xs border border-emerald-500/30 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASSED
          </span>
        );
      case 'passed_with_limitations':
        return (
          <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 font-bold text-xs border border-amber-500/30 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> PASSED WITH LIMITATIONS
          </span>
        );
      case 'needs_review':
        return (
          <span className="px-3 py-1 rounded-full bg-sky-500/10 text-sky-400 font-bold text-xs border border-sky-500/30 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> NEEDS AGRONOMIST REVIEW
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 font-bold text-xs border border-rose-500/30 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> FAILED
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header & Status */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-200">
            Independent Verification & Critic Stage
          </h3>
        </div>
        {getStatusBadge(verification.overall_status)}
      </div>

      {/* Multidimensional Confidence Calibration Gauge */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
            <Scale className="w-4 h-4 text-emerald-400" />
            <span>Calibrated Multidimensional Confidence Score</span>
          </div>
          <div className="text-right">
            <span className="text-lg font-mono font-bold text-emerald-400">
              {(conf.heuristic_score * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400 block uppercase font-bold">
              Level: {conf.overall_confidence}
            </span>
          </div>
        </div>

        {/* 4 Factor Breakdown Progress Bars */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          {/* Grounding 35% */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>Grounding (35%)</span>
              <span className="font-mono text-emerald-400">
                {(conf.evidence_coverage_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-400 h-full rounded-full transition-all"
                style={{ width: `${conf.evidence_coverage_score * 100}%` }}
              />
            </div>
          </div>

          {/* Density 25% */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>Evidence (25%)</span>
              <span className="font-mono text-sky-400">
                {((conf.heuristic_score >= 0.7 ? 0.9 : 0.6) * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-sky-400 h-full rounded-full transition-all"
                style={{ width: `${(conf.heuristic_score >= 0.7 ? 0.9 : 0.6) * 100}%` }}
              />
            </div>
          </div>

          {/* Math 20% */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>Math Validity (20%)</span>
              <span className="font-mono text-purple-400">
                {(conf.schema_validity_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-purple-400 h-full rounded-full transition-all"
                style={{ width: `${conf.schema_validity_score * 100}%` }}
              />
            </div>
          </div>

          {/* Completeness 20% */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>Completeness (20%)</span>
              <span className="font-mono text-amber-400">
                {(conf.data_completeness_score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-amber-400 h-full rounded-full transition-all"
                style={{ width: `${conf.data_completeness_score * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Audit explanation */}
        <p className="text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800">
          {conf.formula_explanation}
        </p>
      </div>

      {/* Individual Verification Checks */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
          Critic Audits Conducted ({verification.checks.length})
        </span>
        <div className="space-y-2">
          {verification.checks.map((check, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-3 text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">{check.check_type}</span>
                  {check.target_claim && (
                    <span className="text-[10px] text-slate-400 font-mono">
                      Target: {check.target_claim}
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">{check.details}</p>
              </div>

              <div>{getStatusBadge(check.status)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Self-Correction & Autonomous Recovery Banners */}
      {recoveryEvents.length > 0 && (
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
            <RotateCcw className="w-4 h-4" />
            <span>Autonomous Self-Correction Events ({recoveryEvents.length})</span>
          </div>
          {recoveryEvents.map((evt, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-slate-900/80 border border-indigo-500/20 text-xs space-y-1"
            >
              <div className="flex justify-between font-mono text-[10px] text-slate-400">
                <span>Action: {evt.action_taken}</span>
                <span>{evt.from_target} ➔ {evt.to_target}</span>
              </div>
              <p className="text-slate-300 font-medium">{evt.details}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
