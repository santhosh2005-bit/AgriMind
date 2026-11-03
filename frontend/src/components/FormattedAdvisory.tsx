import React, { useState, useEffect, useRef } from 'react';
import {
  Volume2,
  Play,
  Pause,
  Square,
  Sparkles,
  CloudSun,
  ShieldAlert,
  Sprout,
  HelpCircle,
} from 'lucide-react';

interface FormattedAdvisoryProps {
  content: string;
  language?: string;
  crop?: string;
}

const LANGUAGE_SPEECH_MAP: Record<string, { code: string; label: string }> = {
  ta: { code: 'ta', label: 'தமிழ்' },
  hi: { code: 'hi', label: 'हिंदी' },
  te: { code: 'te', label: 'తెలుగు' },
  kn: { code: 'kn', label: 'ಕನ್ನಡ' },
  ml: { code: 'ml', label: 'മലയാളം' },
  en: { code: 'en', label: 'English' },
  auto: { code: 'en', label: 'Auto' },
};

/** Deep-cleans markdown + HTML text into natural spoken prose for audio narration */
function stripMarkdownForSpeech(text: string): string {
  let t = text;

  // 1. Remove HTML tags like <br>, <br/>, <b>, <strong>, etc.
  t = t.replace(/<br\s*\/?>/gi, ' ');
  t = t.replace(/<[^>]+>/g, ' ');

  // 2. Remove HTML entities
  t = t.replace(/&nbsp;/g, ' ').replace(/&amp;/g, 'and').replace(/&lt;/g, '').replace(/&gt;/g, '');

  // 3. Remove markdown table delimiter rows (|:---|:---|)
  t = t.replace(/^\s*\|[\s\-:|]+\|.*$/gm, '');

  // 4. Remove table pipe characters (convert to natural comma-pause)
  t = t.replace(/\|/g, ', ');

  // 5. Remove bold / italic markers
  t = t.replace(/\*\*(.*?)\*\*/g, '$1');
  t = t.replace(/\*(.*?)\*/g, '$1');
  t = t.replace(/__(.*?)__/g, '$1');
  t = t.replace(/_(.*?)_/g, '$1');

  // 6. Remove heading markers ## ###
  t = t.replace(/^#{1,6}\s+/gm, '');

  // 7. Remove bullet markers at line start (*, -, •, –, —)
  t = t.replace(/^[\s]*[•\-\–\—\*]\s+/gm, '');

  // 8. Remove numbered list markers at line start (1. 2. 3. or 1) 2))
  t = t.replace(/^\s*\d+[.\)]\s+/gm, '');

  // 9. Remove inline numbering mid-sentence like "<br>2." or ". 2."
  t = t.replace(/[।\.\!\?]\s*\d+[.\)]\s+/g, '. ');

  // 10. Remove code blocks and backticks
  t = t.replace(/```[\s\S]*?```/g, '');
  t = t.replace(/`[^`]*`/g, '');

  // 11. Remove special characters that are unpronounceable
  t = t.replace(/[+\[\]{}\\/~^<>=@#%$]/g, ' ');

  // 12. Replace colons and semicolons with comma-pause (more natural)
  t = t.replace(/[:;]/g, ', ');

  // 13. Replace slashes with 'or'
  t = t.replace(/\//g, ' or ');

  // 14. Replace hyphens used as separators (not within words) with space
  t = t.replace(/\s*[-–—]\s*/g, ' ');

  // 15. Remove parentheses but keep content
  t = t.replace(/[()]/g, ' ');

  // 16. Collapse multiple commas
  t = t.replace(/,\s*,+/g, ',');

  // 17. Collapse multiple spaces / newlines
  t = t.replace(/[ \t]+/g, ' ');
  t = t.replace(/\n+/g, '. ');

  // 18. Clean up orphan punctuation at start of words
  t = t.replace(/\s+[,\.]\s*/g, '. ');

  return t.trim();
}

/** Splits text into natural sentence chunks of ~120-180 characters for smooth streaming audio playback */
function splitTextIntoSentences(text: string): string[] {
  const clean = stripMarkdownForSpeech(text);
  if (!clean) return [];

  // Split by full stops, line breaks, question marks, or exclamation marks
  const rawParts = clean.split(/[\n।\.!\?]+/g);
  const chunks: string[] = [];

  rawParts.forEach((part) => {
    const trimmed = part.trim();
    if (!trimmed) return;

    if (trimmed.length <= 160) {
      chunks.push(trimmed);
    } else {
      // Split by commas or spaces if sentence is very long
      const subParts = trimmed.split(/[,;]+/g);
      subParts.forEach((sp) => {
        const subTrimmed = sp.trim();
        if (subTrimmed) {
          chunks.push(subTrimmed);
        }
      });
    }
  });

  return chunks; // Play all advisory sentences completely without truncation
}

/** Helper to render inline markdown: bold, italic, code, and key metrics */
function renderInlineText(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      const inner = part.slice(2, -2);
      return (
        <strong key={index} className="font-semibold text-emerald-300">
          {inner}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      const inner = part.slice(1, -1);
      return (
        <em
          key={index}
          className="italic text-teal-300 bg-teal-500/10 px-1 py-0.5 rounded text-[13px]"
        >
          {inner}
        </em>
      );
    }
    return part;
  });
}

export const FormattedAdvisory: React.FC<FormattedAdvisoryProps> = ({
  content,
  language = 'en',
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [speechRate, setSpeechRate] = useState<number>(1.0);
  const [currentSentenceIdx, setCurrentSentenceIdx] = useState<number>(0);
  const [totalSentences, setTotalSentences] = useState<number>(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const sentencesQueueRef = useRef<string[]>([]);
  const currentIndexRef = useRef<number>(0);
  const isStoppedRef = useRef<boolean>(true);

  const langConfig =
    LANGUAGE_SPEECH_MAP[(language || 'en').toLowerCase()] || LANGUAGE_SPEECH_MAP.en;

  const stopAudio = () => {
    isStoppedRef.current = true;
    sentencesQueueRef.current = [];

    if (audioRef.current) {
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.onpause = null;
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.src = '';
      audioRef.current = null;
    }

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    setIsPlaying(false);
    setIsPaused(false);
    currentIndexRef.current = 0;
    setCurrentSentenceIdx(0);
  };

  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [content, language]);

  const playSentenceAtIndex = (index: number) => {
    if (isStoppedRef.current || index >= sentencesQueueRef.current.length) {
      stopAudio();
      return;
    }

    currentIndexRef.current = index;
    setCurrentSentenceIdx(index + 1);

    const sentence = sentencesQueueRef.current[index];
    const encoded = encodeURIComponent(sentence);
    const apiBase = import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api` : '/api';
    const audioUrl = `${apiBase}/v1/tools/tts?text=${encoded}&lang=${langConfig.code}`;

    const audio = new Audio(audioUrl);
    audio.playbackRate = speechRate;
    audioRef.current = audio;

    audio.onended = () => {
      if (!isStoppedRef.current) {
        playSentenceAtIndex(index + 1);
      }
    };

    audio.onerror = (e) => {
      console.warn('Audio streaming notice for sentence:', index, e);
      if (!isStoppedRef.current) {
        playSentenceAtIndex(index + 1);
      }
    };

    audio.play().catch((err) => {
      console.warn('Playback error:', err);
      if (!isStoppedRef.current) {
        stopAudio();
      }
    });
  };

  const handleSpeak = () => {
    if (isPaused && audioRef.current) {
      isStoppedRef.current = false;
      audioRef.current.play();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    stopAudio();
    isStoppedRef.current = false;

    const sentences = splitTextIntoSentences(content);
    if (sentences.length === 0) return;

    sentencesQueueRef.current = sentences;
    setTotalSentences(sentences.length);
    setIsPlaying(true);
    setIsPaused(false);

    playSentenceAtIndex(0);
  };

  const handlePause = () => {
    if (audioRef.current && isPlaying) {
      audioRef.current.pause();
      setIsPaused(true);
      setIsPlaying(false);
    }
  };

  const handleStop = () => {
    stopAudio();
  };

  // Structured Section Parser
  const parseContentToSections = (rawText: string) => {

    /** Clean a single display line of HTML tags and raw markdown punctuation for visual rendering */
    const cleanDisplayLine = (line: string): string => {
      return line
        .replace(/<br\s*\/?>/gi, ' ')
        .replace(/<[^>]+>/g, ' ')
        .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/\s+/g, ' ')
        .trim();
    };

    // PRE-PROCESS: Replace <br> with newlines BEFORE splitting so multi-item table cells are parsed correctly
    const preProcessed = rawText
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/&nbsp;/g, ' ');

    // Pre-process: remove table delimiter lines (|:---|) entirely from display
    const filteredLines = preProcessed
      .split('\n')
      .filter((line) => !/^\s*\|[\s\-:|]+\|/.test(line));

    const rawLines = filteredLines;
    const sections: Array<{
      title?: string;
      iconType?: string;
      lines: Array<{
        type: 'heading' | 'bullet' | 'numbered' | 'paragraph';
        content: string;
        number?: string;
      }>;
    }> = [];

    let currentSection: (typeof sections)[0] = { lines: [] };

    rawLines.forEach((line) => {
      const trimmed = cleanDisplayLine(line.trim());
      if (!trimmed) return;

      // Skip table separator lines
      if (/^\|[\s\-:|]+\|/.test(trimmed) || /^[\-:]+$/.test(trimmed)) return;

      const isHeaderLine =
        (trimmed.startsWith('**') && (trimmed.endsWith('**') || trimmed.match(/\*\*\s*[:.]\s*$/)) && trimmed.length > 8) ||
        trimmed.startsWith('### ') ||
        trimmed.startsWith('## ') ||
        // Numbered section headers like "**1. Title (Subtitle):**" 
        (trimmed.startsWith('**') && /^\*\*\d+\./.test(trimmed));

      if (isHeaderLine) {
        if (currentSection.lines.length > 0 || currentSection.title) {
          sections.push(currentSection);
        }
        const cleanTitle = trimmed
          .replace(/^#+\s*/, '')
          .replace(/^\*\*/, '')
          .replace(/\*\*$/, '')
          .replace(/[:\s]+$/, '')  // strip trailing colon/spaces
          .trim();

        let iconType = 'general';
        const lowerTitle = cleanTitle.toLowerCase();
        if (
          lowerTitle.includes('weather') ||
          lowerTitle.includes('வானிலை') ||
          lowerTitle.includes('వాతావరణ') ||
          lowerTitle.includes('मौसम') ||
          lowerTitle.includes('climate')
        ) {
          iconType = 'weather';
        } else if (
          lowerTitle.includes('ipm') ||
          lowerTitle.includes('மேலாண்மை') ||
          lowerTitle.includes('యాజమాన్యం') ||
          lowerTitle.includes('management') ||
          lowerTitle.includes('spray') ||
          lowerTitle.includes('మందు')
        ) {
          iconType = 'spray';
        } else if (
          lowerTitle.includes('why') ||
          lowerTitle.includes('சாத்தியமில்லை') ||
          lowerTitle.includes('కారణాలు') ||
          lowerTitle.includes('causes') ||
          lowerTitle.includes('విశ్లేషణ')
        ) {
          iconType = 'diagnosis';
        } else if (
          lowerTitle.includes('cultural') ||
          lowerTitle.includes('பயிர்') ||
          lowerTitle.includes('పంట') ||
          lowerTitle.includes('practice')
        ) {
          iconType = 'crop';
        }

        currentSection = {
          title: cleanTitle,
          iconType,
          lines: [],
        };
        return;
      }

      // Handle table rows with content: "| Day | Action | Text |" -> treat as bullet
      const tableRowMatch = trimmed.match(/^\|(.*)\|$/);
      if (tableRowMatch) {
        const cells = tableRowMatch[1]
          .split('|')
          .map((c) => c.trim())
          .filter((c) => c && !/^[-:]+$/.test(c));
        if (cells.length > 0) {
          // First cell is label (date/day), rest is content — bold the label
          if (cells.length >= 2) {
            const label = cells[0];
            const body = cells.slice(1).join(' — ');
            currentSection.lines.push({
              type: 'bullet',
              content: `**${label}** — ${body}`,
            });
          } else {
            currentSection.lines.push({
              type: 'bullet',
              content: cells.join(' — '),
            });
          }
        }
        return;
      }

      const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numberedMatch) {
        currentSection.lines.push({
          type: 'numbered',
          number: numberedMatch[1],
          content: numberedMatch[2],
        });
        return;
      }

      const bulletMatch = trimmed.match(/^[•\*\-]\s+(.*)/);
      if (bulletMatch) {
        currentSection.lines.push({
          type: 'bullet',
          content: bulletMatch[1],
        });
        return;
      }

      currentSection.lines.push({
        type: 'paragraph',
        content: trimmed,
      });
    });

    if (currentSection.lines.length > 0 || currentSection.title) {
      sections.push(currentSection);
    }

    return sections;
  };

  const sections = parseContentToSections(content);

  const getSectionIcon = (iconType?: string) => {
    switch (iconType) {
      case 'weather':
        return <CloudSun className="w-4 h-4 text-sky-400" />;
      case 'spray':
        return <ShieldAlert className="w-4 h-4 text-emerald-400" />;
      case 'crop':
        return <Sprout className="w-4 h-4 text-teal-400" />;
      case 'diagnosis':
        return <HelpCircle className="w-4 h-4 text-indigo-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-emerald-400" />;
    }
  };

  const getSectionBadgeStyle = (iconType?: string) => {
    switch (iconType) {
      case 'weather':
        return 'bg-sky-500/10 border-sky-500/30 text-sky-300';
      case 'spray':
        return 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300';
      case 'diagnosis':
        return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300';
      default:
        return 'bg-slate-800/80 border-slate-700 text-slate-200';
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Voice Audio Reader Toolbar */}
      <div className="no-print p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg border ${
              isPlaying
                ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 animate-pulse'
                : 'bg-slate-800 border-slate-700 text-slate-300'
            }`}
          >
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <span>Farmer Voice Reader</span>
                <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
                  {langConfig.label} ({langConfig.code})
                </span>
                {isPlaying && totalSentences > 0 && (
                  <span className="text-[10px] px-2 py-0.2 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/40 font-mono">
                    Sentence {currentSentenceIdx}/{totalSentences}
                  </span>
                )}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              {isPlaying
                ? `Speaking native ${langConfig.label} audio stream out loud...`
                : isPaused
                ? 'Voice narration paused'
                : `Listen to the diagnosis & spray guidance in ${langConfig.label}`}
            </p>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-2">
          {isPlaying ? (
            <button
              type="button"
              onClick={handlePause}
              className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center gap-1.5 transition active:scale-95"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSpeak}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-md active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isPaused ? 'Resume' : 'Listen Now'}</span>
            </button>
          )}

          {(isPlaying || isPaused) && (
            <button
              type="button"
              onClick={handleStop}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium flex items-center gap-1 transition"
              title="Stop playback"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop</span>
            </button>
          )}

          {/* Speed Toggle */}
          <button
            type="button"
            onClick={() => setSpeechRate((prev) => (prev === 1.0 ? 0.85 : 1.0))}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-slate-200 border border-slate-700 text-[10px] font-mono transition"
            title="Toggle speech pace"
          >
            {speechRate === 1.0 ? 'Normal (1x)' : 'Slow & Clear (0.85x)'}
          </button>
        </div>
      </div>

      {/* 2. Structured & Beautifully Rendered Advisory Content */}
      <div className="space-y-4">
        {sections.map((section, sIdx) => {
          const badgeStyle = getSectionBadgeStyle(section.iconType);
          return (
            <div
              key={sIdx}
              className={`rounded-xl bg-slate-900/90 border p-4.5 space-y-3 shadow-sm hover:border-slate-700 transition ${
                section.iconType === 'weather'
                  ? 'border-sky-500/30'
                  : section.iconType === 'spray'
                  ? 'border-emerald-500/40'
                  : section.iconType === 'diagnosis'
                  ? 'border-indigo-500/30'
                  : 'border-slate-800'
              }`}
            >
              {/* Section Header */}
              {section.title && (
                <div className="flex items-center gap-2 pb-2.5 border-b border-slate-800/80">
                  <div className={`p-1.5 rounded-lg border ${badgeStyle}`}>
                    {getSectionIcon(section.iconType)}
                  </div>
                  <h4 className="text-sm font-bold text-white tracking-wide">
                    {section.title}
                  </h4>
                </div>
              )}

              {/* Section Lines */}
              <div className="space-y-2.5 text-xs text-slate-200 leading-relaxed font-sans">
                {section.lines.map((line, lIdx) => {
                  if (line.type === 'numbered') {
                    return (
                      <div key={lIdx} className="flex items-start gap-2.5 pt-1">
                        <span className="shrink-0 w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold text-[11px] flex items-center justify-center font-mono">
                          {line.number}
                        </span>
                        <div className="flex-1 text-[13px] text-slate-100 font-medium">
                          {renderInlineText(line.content)}
                        </div>
                      </div>
                    );
                  }

                  if (line.type === 'bullet') {
                    return (
                      <div
                        key={lIdx}
                        className="flex items-start gap-2.5 pl-2 py-0.5 rounded-lg hover:bg-slate-800/40 transition"
                      >
                        <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2" />
                        <div className="flex-1 text-[13px] text-slate-200 leading-relaxed">
                          {renderInlineText(line.content)}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <p key={lIdx} className="text-[13px] text-slate-300 leading-relaxed">
                      {renderInlineText(line.content)}
                    </p>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
