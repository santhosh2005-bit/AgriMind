import React, { useState, useEffect } from 'react';
import {
  Send,
  MapPin,
  UploadCloud,
  FileText,
  Image as ImageIcon,
  Table,
  Sparkles,
  AlertCircle,
  Eye,
  Trash2,
  Sprout,
  Bug,
  TestTube2,
  CloudSun,
  Layers,
  Trees,
  Mic,
  MicOff,
} from 'lucide-react';
import { uploadMultimodalFile } from '../services/api';

export const DEMO_SAMPLE_FILES = [
  {
    metadata: {
      modality: 'image',
      filename: 'tomato_leaf_sample.jpg',
      file_size_bytes: 7759,
      checksum_sha256: 'a1b2c3d4e5f67890abcdef1234567890abcdef12',
      extracted_summary: 'Image 1200x800px. Green canopy: 68.2%, Chlorosis: 24.5%. Blur score: 215.4.',
    },
    processing_summary: {
      width: 1200,
      height: 800,
      color_metrics: {
        green_canopy_pct: 68.2,
        yellow_chlorosis_pct: 24.5,
        chlorosis_severity_ratio: 0.359,
      },
      laplacian_blur_score: 215.4,
      preview_url: 'http://127.0.0.1:8000/data/sample_inputs/images/tomato_leaf_sample.jpg',
    },
  },
  {
    metadata: {
      modality: 'pdf',
      filename: 'ICAR_Tomato_Advisory_Sample.pdf',
      file_size_bytes: 1207,
      checksum_sha256: 'b2c3d4e5f67890abcdef1234567890abcdef1234',
      extracted_summary: 'PDF with 2 pages. Topics: Tomato Early Blight (Alternaria solani), Copper Oxychloride spray guidelines.',
    },
    processing_summary: {
      total_pages: 2,
      detected_topics: ['Tomato Early Blight', 'Fungicidal Spray Guidelines'],
      preview_url: 'http://127.0.0.1:8000/data/sample_inputs/documents/ICAR_Tomato_Advisory_Sample.pdf',
    },
  },
];

export interface WorkspaceSubmission {
  query: string;
  location: string;
  targetLanguage: string;
  uploadedInputs: Array<{
    modality: string;
    filename: string;
    file_size_bytes: number;
    checksum_sha256: string;
    extracted_summary?: string;
  }>;
  files?: Array<{
    metadata: {
      modality: string;
      filename: string;
      file_size_bytes: number;
      checksum_sha256: string;
      extracted_summary?: string;
    };
    processing_summary: Record<string, any>;
  }>;
}

interface RequestWorkspaceProps {
  onRunWorkflow: (sub: WorkspaceSubmission) => void;
  onPreviewPlan: (sub: WorkspaceSubmission) => void;
  isLoading: boolean;
  selectedLanguage: string;
  initialQuery?: string;
}

// Section 3.B: Compact agricultural quick actions for the 6 specified categories
export const AGRICULTURAL_QUICK_ACTIONS = [
  {
    category: 'Crop Health',
    icon: Sprout,
    label: 'Crop Health',
    query: 'Tomato plants in open fields showing lower leaf yellowing with concentric brown rings. Check current weather conditions and recommend IPM spray dosage.',
    location: 'Nashik, Maharashtra',
    lang: 'auto',
  },
  {
    category: 'Pest & Disease',
    icon: Bug,
    label: 'Pest & Disease (Tamil Demo)',
    query: 'My tomato plants have yellow leaves. I am uploading a crop photograph and a soil report. Check relevant weather conditions for my location, compare the evidence with agricultural guidance, and recommend practical next steps. Respond in Tamil.',
    location: 'Madurai, Tamil Nadu',
    lang: 'ta',
  },
  {
    category: 'Soil & Fertilizers',
    icon: TestTube2,
    label: 'Soil & Fertilizers',
    query: 'Farm parcel P-101 has alkaline soil pH 7.8 and salinity EC 2.4 dS/m. What soil amendment and nutrient management plan is recommended?',
    location: 'Nagpur, Maharashtra',
    lang: 'auto',
  },
  {
    category: 'Weather & Irrigation',
    icon: CloudSun,
    label: 'Weather & Irrigation',
    query: 'Forecast shows high temperatures above 36°C with low relative humidity. How should I adjust drip irrigation schedules to prevent blossom end rot in tomatoes?',
    location: 'Pune, Maharashtra',
    lang: 'auto',
  },
  {
    category: 'Crop Recommendations',
    icon: Layers,
    label: 'Crop Recommendations',
    query: 'Given red loamy soil with moderate rainfall and upcoming winter season, which high-yield pulse or vegetable crops are most viable?',
    location: 'Coimbatore, Tamil Nadu',
    lang: 'auto',
  },
  {
    category: 'Farming Practices',
    icon: Trees,
    label: 'Farming Practices',
    query: 'What are the recommended mulching and staking practices for indeterminate tomatoes to prevent soil-borne fungal splash and fruit rot?',
    location: 'Karnal, Haryana',
    lang: 'auto',
  },
];

export const RequestWorkspace: React.FC<RequestWorkspaceProps> = ({
  onRunWorkflow,
  onPreviewPlan,
  isLoading,
  selectedLanguage,
  initialQuery,
}) => {
  const [query, setQuery] = useState(initialQuery || AGRICULTURAL_QUICK_ACTIONS[1].query);
  const [location, setLocation] = useState(AGRICULTURAL_QUICK_ACTIONS[1].location);

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{
    metadata: {
      modality: string;
      filename: string;
      file_size_bytes: number;
      checksum_sha256: string;
      extracted_summary?: string;
    };
    processing_summary: Record<string, any>;
  }>>(DEMO_SAMPLE_FILES);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Speech Recognition state for multilingual voice queries
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);

  const getLanguageSpeechCode = (lang: string): string => {
    switch (lang.toLowerCase()) {
      case 'ta':
        return 'ta-IN';
      case 'hi':
        return 'hi-IN';
      case 'te':
        return 'te-IN';
      case 'kn':
        return 'kn-IN';
      case 'ml':
        return 'ml-IN';
      case 'en':
      case 'auto':
      default:
        return 'en-IN';
    }
  };

  const handleToggleVoiceInput = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechError('Voice input requires Chrome, Edge, or a Web Speech API compatible browser.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = getLanguageSpeechCode(selectedLanguage);
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechError(null);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          setQuery((prev) => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event: any) => {
        setIsListening(false);
        if (event.error !== 'no-speech') {
          setSpeechError(`Voice error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err: any) {
      setIsListening(false);
      setSpeechError(err.message || 'Could not start voice recognition');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // File validation: Size limit 15MB
    if (file.size > 15 * 1024 * 1024) {
      setUploadError(`File '${file.name}' exceeds maximum supported size (15 MB).`);
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    try {
      const result = await uploadMultimodalFile(file);
      setUploadedFiles((prev) => [...prev, result]);
    } catch (err: any) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSelectQuickAction = (action: (typeof AGRICULTURAL_QUICK_ACTIONS)[0]) => {
    setQuery(action.query);
    setLocation(action.location);
    if (action.category === 'Pest & Disease') {
      setUploadedFiles(DEMO_SAMPLE_FILES);
    }
  };

  const getSubmissionPayload = (): WorkspaceSubmission => ({
    query: query.trim(),
    location: location.trim(),
    targetLanguage: selectedLanguage,
    uploadedInputs: uploadedFiles.map((f) => f.metadata),
    files: uploadedFiles,
  });

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-600/5 rounded-full blur-3xl pointer-events-none" />

      {/* Section 3.B: Welcome Screen Banner */}
      <div className="mb-5 pb-4 border-b border-slate-800/80">
        <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          <span>Welcome to AgriMind</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1 leading-relaxed">
          Ask questions about your crops, soil, pests, weather, or farming practices. Upload photographs and agricultural documents to receive evidence-backed guidance.
        </p>
      </div>

      {/* Section 3.B: Compact Agricultural Quick Actions */}
      <div className="mb-5">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Agricultural Quick Actions</span>
          </div>
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            Populates example agricultural prompts
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {AGRICULTURAL_QUICK_ACTIONS.map((action, idx) => {
            const IconComponent = action.icon;
            const isSelected = query === action.query;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectQuickAction(action)}
                className={`text-xs p-2.5 rounded-xl border transition flex flex-col items-center justify-center text-center gap-1.5 active:scale-95 ${
                  isSelected
                    ? 'bg-emerald-500/15 border-emerald-500/50 text-emerald-300 shadow-sm'
                    : 'bg-slate-900/90 hover:bg-slate-850 text-slate-300 hover:text-emerald-300 border-slate-800 hover:border-emerald-500/40'
                }`}
                title={action.query}
              >
                <IconComponent className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="font-medium text-[11px] line-clamp-1">{action.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Query Textarea (Section 3.D: Multiline natural-language input) */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <label htmlFor="user-query-input" className="block text-xs font-semibold text-slate-300">
            Agricultural Inquiry or Problem Description:
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleToggleVoiceInput}
              className={`text-xs px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition ${
                isListening
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/50 animate-pulse'
                  : 'bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 border-slate-700'
              }`}
              title={`Voice Input (${getLanguageSpeechCode(selectedLanguage)})`}
            >
              {isListening ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  <MicOff className="w-3.5 h-3.5 text-rose-400" />
                  <span className="font-medium text-[11px]">Listening ({getLanguageSpeechCode(selectedLanguage)})...</span>
                </>
              ) : (
                <>
                  <Mic className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="font-medium text-[11px]">Voice Input</span>
                </>
              )}
            </button>
          </div>
        </div>

        <textarea
          id="user-query-input"
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe symptoms, crop conditions, soil properties, weather questions, or farming practices..."
          className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition resize-none"
        />

        {speechError && (
          <p className="mt-1 text-[11px] text-amber-400 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 shrink-0" />
            <span>{speechError}</span>
          </p>
        )}
      </div>

      {/* Location Context & Multimodal Attachment Row (Section 3.D) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {/* Optional Location Input */}
        <div>
          <label htmlFor="location-context-input" className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>Farm Location (Optional for weather & thermal risk):</span>
          </label>
          <input
            id="location-context-input"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Nashik, Maharashtra (not required for general questions)"
            className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
          />
        </div>

        {/* Supported Upload Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <UploadCloud className="w-3.5 h-3.5 text-emerald-400" />
            <span>Attach Crop Photo, Soil Report (PDF/CSV):</span>
          </label>
          <div className="flex items-center gap-2">
            <label className="flex-1 flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-850 border border-dashed border-slate-700 hover:border-emerald-500/50 cursor-pointer transition text-xs text-slate-300">
              <UploadCloud className="w-4 h-4 text-emerald-400" />
              <span>{isUploading ? 'Validating...' : 'Upload Image / PDF / CSV'}</span>
              <input
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.pdf,.csv,.json"
                onChange={handleFileUpload}
                disabled={isUploading}
                className="hidden"
              />
            </label>
            <button
              type="button"
              onClick={() => setUploadedFiles(DEMO_SAMPLE_FILES)}
              className="px-3 py-2 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition shrink-0 flex items-center gap-1.5"
              title="Attach sample tomato leaf photograph and ICAR advisory PDF"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Sample Files</span>
            </button>
          </div>
        </div>
      </div>

      {/* Upload Error Banner */}
      {uploadError && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Visible list of selected attachments with clear removal controls (Section 3.D) */}
      {uploadedFiles.length > 0 && (
        <div className="mb-5 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Selected Attachments ({uploadedFiles.length})
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {uploadedFiles.map((file, idx) => {
              const meta = file.metadata;
              const summary = file.processing_summary;
              const isImage = meta.modality === 'image';
              const isPdf = meta.modality === 'pdf';
              const isTabular = meta.modality === 'csv' || meta.modality === 'json';

              return (
                <div
                  key={idx}
                  className="rounded-xl bg-slate-900/90 border border-slate-800 p-3.5 text-xs space-y-1.5 relative group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-medium text-slate-200">
                      {isImage && <ImageIcon className="w-4 h-4 text-emerald-400" />}
                      {isPdf && <FileText className="w-4 h-4 text-sky-400" />}
                      {isTabular && <Table className="w-4 h-4 text-amber-400" />}
                      <span className="truncate max-w-[180px]">{meta.filename}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[10px]">
                        {(meta.file_size_bytes / 1024).toFixed(1)} KB
                      </span>
                      {/* Clear attachment removal button */}
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(idx)}
                        className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Remove attachment"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Preprocessor Inspection Badge */}
                  {isImage && summary.color_metrics && (
                    <div className="text-slate-400 text-[11px] space-y-0.5">
                      <div className="flex justify-between">
                        <span>Resolution: {summary.width}x{summary.height}</span>
                        <span className={summary.is_blurry ? 'text-amber-400' : 'text-emerald-400'}>
                          Clarity: {summary.laplacian_blur_score?.toFixed(1) || 'N/A'}
                        </span>
                      </div>
                      <div className="flex gap-2 text-[10px]">
                        <span className="text-emerald-400">Canopy: {summary.color_metrics.green_canopy_pct}%</span>
                        <span className="text-amber-300">Chlorosis: {summary.color_metrics.yellow_chlorosis_pct}%</span>
                        <span className="text-rose-400">Severity: {summary.color_metrics.chlorosis_severity_ratio}</span>
                      </div>
                    </div>
                  )}

                  {isPdf && summary.total_pages && (
                    <div className="text-slate-400 text-[11px]">
                      <span>Extracted: {summary.total_pages} page(s), {summary.total_words} words. Content verified.</span>
                    </div>
                  )}

                  {isTabular && summary.summary && (
                    <div className="text-slate-400 text-[11px] space-y-0.5">
                      <span>Rows: {summary.summary.row_count} | Columns: {summary.summary.columns?.slice(0, 4).join(', ')}...</span>
                      {summary.diagnostic_insights?.length > 0 && (
                        <p className="text-amber-300 font-medium">{summary.diagnostic_insights[0]}</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={() => onPreviewPlan(getSubmissionPayload())}
          disabled={isLoading || !query.trim()}
          className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 transition text-xs font-semibold flex items-center gap-2 disabled:opacity-50 active:scale-95"
          title="Preview the dependency-aware DAG before execution"
        >
          <Eye className="w-4 h-4 text-emerald-400" />
          <span>Preview Plan DAG</span>
        </button>

        <button
          type="button"
          onClick={() => onRunWorkflow(getSubmissionPayload())}
          disabled={isLoading || !query.trim()}
          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-500 hover:from-emerald-500 hover:to-green-400 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/25 transition disabled:opacity-50 active:scale-95"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Orchestrating Multi-Model DAG...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Consult AgriMind Advisor</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
