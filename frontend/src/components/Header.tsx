import React from 'react';
import { Sprout, RefreshCw, History, Globe2 } from 'lucide-react';
import type { SystemHealth } from '../types/api';

export const LANGUAGE_OPTIONS = [
  { code: 'auto', label: 'Auto Detect (தானியங்கு)', native: 'Auto' },
  { code: 'en', label: 'English', native: 'English' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
];

interface HeaderProps {
  health: SystemHealth | null;
  isLoading: boolean;
  selectedLanguage: string;
  onSelectLanguage: (lang: string) => void;
  onRefreshHealth: () => void;
  onOpenHistory: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isLoading,
  selectedLanguage,
  onSelectLanguage,
  onRefreshHealth,
  onOpenHistory,
}) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sprout className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 via-green-300 to-teal-200 bg-clip-text text-transparent">
                AgriMind
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Your Intelligent Agricultural Companion
            </p>
          </div>
        </div>

        {/* Controls: Language Selector, History, Discreet Connectivity Indicator */}
        <div className="flex items-center gap-3">
          {/* Preferred Response-Language Selector */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <Globe2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <select
              value={selectedLanguage}
              onChange={(e) => onSelectLanguage(e.target.value)}
              className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer pr-1 text-xs"
              title="Preferred Response Language"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.code} value={opt.code} className="bg-slate-900 text-slate-200">
                  {opt.native} ({opt.label.split(' ')[0]})
                </option>
              ))}
            </select>
          </div>

          {/* Conversation History Control */}
          <button
            onClick={onOpenHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 transition text-xs font-medium"
            title="View Past Conversation & Diagnostic History"
          >
            <History className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">History</span>
          </button>

          {/* Discreet Backend Connectivity Indicator */}
          <button
            onClick={onRefreshHealth}
            title={isHealthy ? `Backend Connected (${health?.registered_models_count || 4} models ready)` : 'Connecting to backend...'}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-850 border border-slate-800/80 transition text-xs"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  : 'bg-amber-400 animate-pulse'
              }`}
            />
            <span className="text-slate-400 text-[11px] hidden md:inline">
              {isLoading ? 'Checking...' : isHealthy ? 'Connected' : 'Offline'}
            </span>
            <RefreshCw className={`w-3 h-3 text-slate-500 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
