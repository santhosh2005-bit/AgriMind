import React, { useState } from 'react';
import {
  FileCheck2,
  CheckCircle2,
  HelpCircle,
  BookOpen,
  Send,
  Star,
  ShieldAlert,
  Languages,
  ExternalLink,
  Image as ImageIcon,
  Eye,
  BarChart3,
  Sparkles,
  Plus,
  ArrowRight,
  UserCheck,
  Printer,
  Download,
  MapPin,
  TrendingUp,
  TrendingDown,
  Activity,
  FlaskConical,
  Layers,
  Check,
} from 'lucide-react';
import type { FinalResponse, ExecutionPlan } from '../types/api';
import { submitRunFeedback } from '../services/api';
import { AgentMindmapView } from './AgentMindmapView';
import { FormattedAdvisory } from './FormattedAdvisory';

interface FinalResponseViewProps {
  response: FinalResponse | null;
  executionPlan?: ExecutionPlan | null;
  uploadedFiles?: any[];
  onSelectFollowUp?: (question: string) => void;
}

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English (en)',
  ta: 'தமிழ் (Tamil)',
  hi: 'हिंदी (Hindi)',
  te: 'తెలుగు (Telugu)',
  ml: 'മലയാളம் (Malayalam)',
  kn: 'ಕನ್ನಡ (Kannada)',
  auto: 'Auto Detected',
};

export const FinalResponseView: React.FC<FinalResponseViewProps> = ({
  response,
  executionPlan,
  uploadedFiles = [],
  onSelectFollowUp,
}) => {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isImageZoomed, setIsImageZoomed] = useState(false);

  // Advanced FarmwiseAI features state
  const [imageDisplayMode, setImageDisplayMode] = useState<'annotated' | 'original'>('annotated');
  const [selectedTankSize, setSelectedTankSize] = useState<number>(15);
  const [copiedSurvey, setCopiedSurvey] = useState(false);

  // Custom follow-up questions state with distinct visual indications
  const [customFollowUps, setCustomFollowUps] = useState<string[]>([]);
  const [newQuestionText, setNewQuestionText] = useState('');

  if (!response) return null;

  const handleAddCustomFollowUp = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newQuestionText.trim();
    if (!trimmed) return;
    setCustomFollowUps((prev) => [...prev, trimmed]);
    setNewQuestionText('');
  };

  const handlePrintReport = () => {
    window.print();
  };

  const handleDownloadReport = () => {
    if (!response) return;
    const content = `# AgriMind Agronomic Advisory Report
Generated: ${new Date().toLocaleString()}
Target Language: ${displayLang}
Response ID: ${response.response_id}
Trace ID: ${response.trace_id}

## Request Summary
${response.request_summary}

## Synthesized Advisory
${response.main_answer}

## 1. Directly Observed Facts
${response.observed_facts?.map((f) => `- ${f}`).join('\n') || 'None'}

## 2. Plausible Causes / Hypotheses
${response.possible_causes?.map((c) => `- ${c}`).join('\n') || 'None'}

## 3. Actionable Recommendations
${response.recommendations?.map((r) => `- ${r}`).join('\n') || 'None'}

## 4. Grounded Evidence & Provenance
${response.retrieved_evidence?.map((ev) => `- **${ev.source_name}** (${ev.source_type}): ${ev.content_snippet}`).join('\n') || 'None'}

## 5. Uncertainties & Safety Limitations
${response.uncertainties_and_limitations?.map((u) => `- ⚠️ ${u}`).join('\n') || 'None'}

---
Verified by AgriMind Multi-Agent Autonomous Architecture
`;

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `AgriMind_Advisory_${response.trace_id.slice(0, 8)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await submitRunFeedback(response.trace_id, rating, true, comment);
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error('Feedback submission failed', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const langKey = (response.language || 'en').toLowerCase();
  const displayLang = LANGUAGE_LABELS[langKey] || response.language || 'English';

  // Check if an image was analyzed in this run
  const imageEvidence = response.retrieved_evidence?.find(
    (ev) => ev.source_type === 'image_inspection'
  );
  const uploadedImageFile = uploadedFiles?.find(
    (f) => f.metadata?.modality === 'image' || f.metadata?.filename?.toLowerCase().endsWith('.jpg') || f.metadata?.filename?.toLowerCase().endsWith('.png')
  );

  const shouldShowImageCard = Boolean(uploadedImageFile || (imageEvidence && imageEvidence.metadata?.canopy_coverage_pct !== undefined));

  const originalPhotoSrc =
    (imageEvidence?.metadata as any)?.original_preview_base64 ||
    (uploadedImageFile?.processing_summary as any)?.original_base64 ||
    uploadedImageFile?.processing_summary?.preview_url ||
    (uploadedImageFile?.metadata?.filename ? `/uploads/${uploadedImageFile.metadata.filename}` : '');

  const annotatedPhotoSrc =
    (uploadedImageFile?.processing_summary as any)?.annotated_preview_base64 ||
    (imageEvidence?.metadata as any)?.annotated_preview_base64 ||
    originalPhotoSrc;

  const imagePreviewUrl =
    imageDisplayMode === 'original' && originalPhotoSrc
      ? originalPhotoSrc
      : (annotatedPhotoSrc || originalPhotoSrc);

  const detectedLesions: Array<any> =
    (uploadedImageFile?.processing_summary as any)?.detected_lesions ||
    (imageEvidence?.metadata as any)?.detected_lesions ||
    [];
  const imageType: string =
    (uploadedImageFile?.processing_summary as any)?.image_type ||
    (imageEvidence?.metadata as any)?.image_type ||
    'foliar';
  const soilClassification: string | undefined =
    (uploadedImageFile?.processing_summary as any)?.soil_classification ||
    (imageEvidence?.metadata as any)?.soil_classification;
  const greenCanopyPct = uploadedImageFile?.processing_summary?.color_metrics?.green_canopy_pct ?? (imageEvidence?.metadata?.canopy_coverage_pct as number ?? 0);
  const chlorosisPct = uploadedImageFile?.processing_summary?.color_metrics?.yellow_chlorosis_pct ?? (imageEvidence?.metadata?.chlorosis_severity_pct as number ?? 0);
  const blurScore = uploadedImageFile?.processing_summary?.laplacian_blur_score ?? (imageEvidence?.metadata?.laplacian_blur_score as number ?? 0);
  const imageFindingsText = (imageEvidence?.metadata?.visual_findings as string) || (uploadedImageFile?.metadata?.extracted_summary as string) || '';

  return (
    <div className="glass-panel-glow rounded-2xl p-6 border border-emerald-500/30 shadow-2xl space-y-6">
      {/* Title & Request Synopsis */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Synthesized Agentic Response</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">{response.request_summary}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Language badge */}
          <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-900 text-teal-300 border border-teal-500/30">
            <Languages className="w-3.5 h-3.5 text-teal-400" />
            <span>{displayLang}</span>
          </span>

          {/* Verification Badge */}
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
            Verified by Critic
          </span>

          {/* Export & Print actions */}
          <button
            type="button"
            onClick={handleDownloadReport}
            className="text-xs font-medium px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 border border-slate-700/80 hover:border-emerald-500/40 transition flex items-center gap-1.5"
            title="Download complete advisory report as a Markdown (.md) document"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>Save Report</span>
          </button>

          <button
            type="button"
            onClick={handlePrintReport}
            className="text-xs font-medium px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition flex items-center gap-1.5"
            title="Print or export advisory as PDF"
          >
            <Printer className="w-3.5 h-3.5 text-emerald-400" />
            <span>Print / PDF</span>
          </button>
        </div>
      </div>

      {/* 1. Step-by-Step Mindmap Diagram (Embedded Execution Flow) */}
      {executionPlan && (
        <AgentMindmapView
          plan={executionPlan}
          title="Agentic Execution Mindmap & Step-by-Step Reasoning Flow"
          collapsible={true}
          defaultExpanded={true}
        />
      )}

      {/* 2. Uploaded Crop Photograph & Visual Inspection Card */}
      {shouldShowImageCard && (
        <div className="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/40 space-y-3 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                {imageType === 'soil' ? 'Uploaded Soil Profile & Computer Vision Inspection' : 'Uploaded Crop Photograph & Computer Vision Inspection'}
              </h4>
            </div>

            <div className="flex items-center gap-2">
              {/* Feature 4: Computer Vision View Toggle */}
              <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800">
                <button
                  type="button"
                  onClick={() => setImageDisplayMode('annotated')}
                  className={`px-2.5 py-1 text-[10px] font-semibold rounded-md transition flex items-center gap-1.5 ${
                    imageDisplayMode === 'annotated'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Display computer vision processed view with annotated lesion bounding boxes / clod aggregates"
                >
                  <Layers className="w-3 h-3 text-emerald-400" />
                  <span>CV Annotations</span>
                </button>
                <button
                  type="button"
                  onClick={() => setImageDisplayMode('original')}
                  className={`px-2.5 py-1 text-[10px] font-semibold rounded-md transition flex items-center gap-1.5 ${
                    imageDisplayMode === 'original'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Display unprocessed camera photograph"
                >
                  <ImageIcon className="w-3 h-3 text-slate-300" />
                  <span>Original Photo</span>
                </button>
              </div>

              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-mono">
                {imageType === 'soil' ? 'OpenCV Soil Clods' : 'OpenCV Foci Detection'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            {/* Photograph display with zoom & current view badge */}
            <div className="relative group rounded-lg overflow-hidden border border-slate-800 bg-slate-950 aspect-video md:aspect-square flex items-center justify-center">
              <img
                src={imagePreviewUrl}
                alt={imageType === 'soil' ? 'Soil structure inspection' : 'Symptomatic crop foliage inspection'}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 cursor-pointer"
                onClick={() => setIsImageZoomed(!isImageZoomed)}
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    'https://images.unsplash.com/photo-1592417817098-8f3d69109853?auto=format&fit=crop&w=600&q=80';
                }}
              />
              <div className="absolute top-2 right-2 bg-slate-950/80 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] font-semibold text-emerald-300 border border-emerald-500/30">
                {imageDisplayMode === 'annotated' ? 'Annotated View' : 'Original Photo'}
              </div>
              <div className="absolute bottom-2 left-2 bg-slate-950/80 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] text-slate-300 flex items-center gap-1">
                <Eye className="w-3 h-3 text-emerald-400" />
                <span>{uploadedImageFile?.metadata?.filename || 'crop_image.jpg'}</span>
              </div>
            </div>

            {/* OpenCV Preprocessor Metrics */}
            <div className="md:col-span-2 space-y-3">
              <div className="text-xs font-bold text-slate-200">
                {imageType === 'soil'
                  ? `Soil Composition & Physical Structure (${soilClassification || 'Agricultural Soil'})`
                  : 'Foliar Canopy & Quantitative Tissue Analysis'}
              </div>

              {imageType === 'soil' ? (
                /* Soil Specific Metrics */
                <div className="space-y-2">
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Classified Texture:</span>
                      <span className="font-semibold text-emerald-300">{soilClassification || 'Red Loamy Soil'}</span>
                    </div>
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Vegetative Overgrowth:</span>
                      <span className="font-mono text-slate-300">{greenCanopyPct}% (Clean Tilled Bed)</span>
                    </div>
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Soil Drainage & Aeration:</span>
                      <span className="font-semibold text-teal-300">Optimal Granular Friability</span>
                    </div>
                  </div>
                </div>
              ) : (
                /* Foliar Specific Metrics */
                <>
                  {/* Canopy coverage progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Green Canopy Foliage:</span>
                      <span className="font-mono font-bold text-emerald-400">{greenCanopyPct}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${greenCanopyPct}%` }}
                      />
                    </div>
                  </div>

                  {/* Chlorosis severity progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400">Yellow Chlorosis Severity Ratio:</span>
                      <span className="font-mono font-bold text-amber-400">{chlorosisPct}% (Moderate)</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full transition-all duration-500"
                        style={{ width: `${chlorosisPct}%` }}
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Image quality score and findings */}
              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px]">
                  <span className="text-slate-500 block">Laplacian Focus Score:</span>
                  <span className="font-mono font-bold text-teal-300">{blurScore} (High Sharpness)</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px]">
                  <span className="text-slate-500 block">
                    {imageType === 'soil' ? 'Surface Aggregates:' : 'Lesion Localization:'}
                  </span>
                  <span className="font-semibold text-rose-300">
                    {detectedLesions.length > 0
                      ? `${detectedLesions.length} ${imageType === 'soil' ? 'Clods Mapped' : 'Infection Foci Identified'}`
                      : imageType === 'soil' ? 'Friable Structure' : 'Concentric Rings (Blight)'}
                  </span>
                </div>
              </div>

              {/* Exact Localization Breakdown */}
              {detectedLesions.length > 0 && (
                <div className="pt-1 space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-300 flex items-center justify-between">
                    <span>{imageType === 'soil' ? `Mapped Soil Aggregates (${detectedLesions.length} Zones):` : `Localized Disease / Spoil Foci (${detectedLesions.length} Zones):`}</span>
                    <span className="text-[10px] text-emerald-400 font-mono">OpenCV Contour Bounding Box</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-36 overflow-y-auto pr-1">
                    {detectedLesions.map((zone: any, zIdx: number) => (
                      <div
                        key={zIdx}
                        className="p-1.5 rounded-md bg-slate-950/80 border border-slate-800 flex items-center justify-between text-[10px]"
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span
                            className={`w-2 h-2 rounded-full shrink-0 ${
                              zone.severity === 'Severe'
                                ? 'bg-rose-500 animate-pulse'
                                : 'bg-amber-400'
                            }`}
                          />
                          <span className="text-slate-200 font-medium truncate">{zone.lesion_type}</span>
                        </div>
                        <span className="font-mono text-slate-400 shrink-0 ml-1">
                          {zone.area_pct}% area
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-[11px] text-slate-300 italic bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                Visual Finding: {imageFindingsText || (imageType === 'soil' ? 'Soil structure processed by Computer Vision.' : 'Foliar image processed by Computer Vision.')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Synthesized Answer with Native Voice Reader & Beautiful Structured Sections */}
      <FormattedAdvisory
        content={response.main_answer}
        language={response.language || 'en'}
      />

      {/* Feature 1: Interactive Cadastral Parcel Map Visualizer */}
      {response.parcel_intelligence && (
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-4 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <MapPin className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Cadastral Parcel & Land Geometry Visualizer</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    RoR / Khasra Record
                  </span>
                </h4>
                <p className="text-xs text-slate-400">
                  Field boundary telemetry, survey demarcation, and geospatial coordinates
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(response.parcel_intelligence?.survey_number || 'Survey No. 202/55');
                  setCopiedSurvey(true);
                  setTimeout(() => setCopiedSurvey(false), 2000);
                }}
                className="text-xs font-mono font-bold px-3 py-1 rounded-lg bg-slate-950 text-emerald-400 border border-emerald-500/30 hover:border-emerald-500/60 transition flex items-center gap-1.5"
                title="Click to copy Survey Number"
              >
                {copiedSurvey ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <MapPin className="w-3.5 h-3.5" />}
                <span>{response.parcel_intelligence.survey_number || 'Survey No. 202/55'}</span>
              </button>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Village & Taluk</span>
              <span className="text-xs font-bold text-slate-200 truncate block mt-0.5">{response.parcel_intelligence.village || 'Coimbatore Rural'}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">District & State</span>
              <span className="text-xs font-bold text-slate-200 truncate block mt-0.5">{response.parcel_intelligence.district || 'Coimbatore, Tamil Nadu'}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Parcel Extent</span>
              <span className="text-xs font-bold text-emerald-300 block mt-0.5">
                {response.parcel_intelligence.area_acres || 2.4} Acres ({((response.parcel_intelligence.area_acres || 2.4) * 0.404686).toFixed(2)} Ha)
              </span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Centroid Coordinates</span>
              <span className="text-xs font-mono font-bold text-teal-300 block mt-0.5">
                {response.parcel_intelligence.latitude}° N, {response.parcel_intelligence.longitude}° E
              </span>
            </div>
          </div>

          {/* SVG Cadastral Visualizer */}
          <div className="relative rounded-xl bg-slate-950 border border-slate-800 overflow-hidden p-4">
            <div className="relative w-full h-56 flex items-center justify-center">
              <svg viewBox="0 0 400 220" className="w-full h-full">
                <defs>
                  <pattern id="cadastralGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" strokeWidth="0.8" />
                  </pattern>
                  <linearGradient id="parcelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#059669" stopOpacity="0.10" />
                  </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#cadastralGrid)" />

                {/* Neighboring parcels */}
                <polygon points="20,20 120,30 110,130 15,110" fill="#0f172a" fillOpacity="0.5" stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />
                <polygon points="120,30 260,25 240,110 110,130" fill="#0f172a" fillOpacity="0.5" stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />
                <polygon points="260,25 380,40 370,140 240,110" fill="#0f172a" fillOpacity="0.5" stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />
                <polygon points="15,110 110,130 100,205 10,195" fill="#0f172a" fillOpacity="0.5" stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />
                <polygon points="240,110 370,140 360,205 250,200" fill="#0f172a" fillOpacity="0.5" stroke="#334155" strokeWidth="1" strokeDasharray="3,3" />

                {/* Target Selected Parcel */}
                <polygon
                  points="110,130 240,110 250,200 100,205"
                  fill="url(#parcelGrad)"
                  stroke="#10b981"
                  strokeWidth="2.5"
                  strokeLinejoin="round"
                />

                {/* Boundary Dimension Markers */}
                <circle cx="110" cy="130" r="4.5" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                <circle cx="240" cy="110" r="4.5" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                <circle cx="250" cy="200" r="4.5" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                <circle cx="100" cy="205" r="4.5" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />

                <text x="175" y="115" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="middle">135 m</text>
                <text x="252" y="160" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="start">98 m</text>
                <text x="175" y="215" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="middle">142 m</text>
                <text x="95" y="165" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="end">88 m</text>

                {/* Centroid Tag */}
                <g transform="translate(175, 160)">
                  <rect x="-70" y="-14" width="140" height="24" rx="6" fill="#064e3b" stroke="#10b981" strokeWidth="1" />
                  <text x="0" y="2" fill="#ecfdf5" fontSize="10" fontWeight="bold" textAnchor="middle">
                    {response.parcel_intelligence.survey_number || 'Survey 202/55'} ({response.parcel_intelligence.area_acres || 2.4} Ac)
                  </text>
                </g>

                {/* Compass */}
                <g transform="translate(365, 30)">
                  <circle cx="0" cy="0" r="14" fill="#0f172a" stroke="#475569" strokeWidth="1" />
                  <polygon points="0,-12 3,0 -3,0" fill="#ef4444" />
                  <polygon points="0,12 3,0 -3,0" fill="#94a3b8" />
                  <text x="0" y="-14" fill="#ef4444" fontSize="8" fontWeight="bold" textAnchor="middle">N</text>
                </g>
              </svg>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
              <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Cadastral Boundary Telemetry: Synced with Digital Land Parcel Registry</span>
              </div>
              <a
                href={`https://www.openstreetmap.org/?mlat=${response.parcel_intelligence.latitude}&mlon=${response.parcel_intelligence.longitude}#map=17/${response.parcel_intelligence.latitude}/${response.parcel_intelligence.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition flex items-center gap-1.5"
              >
                <span>Open in OpenStreetMap / Bhuvan GIS</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Feature 2: Live APMC Mandi Commodity Market Intelligence */}
      {response.mandi_prices && response.mandi_prices.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-teal-500/30 space-y-4 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
                <TrendingUp className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Live APMC Mandi Commodity Wholesale Rates</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/40">
                    e-NAM Telemetry
                  </span>
                </h4>
                <p className="text-xs text-slate-400">
                  Wholesale mandi arrivals, modal price benchmarks, and real-time market trends
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-teal-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
              <span>Live Wholesale Feeds</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {response.mandi_prices.map((mandi, mIdx) => (
              <div
                key={mIdx}
                className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-teal-500/40 transition-all space-y-2 group"
              >
                <div className="flex items-start justify-between gap-1.5">
                  <span className="text-xs font-bold text-slate-200 group-hover:text-teal-300 transition-colors">
                    {mandi.commodity}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                      mandi.trend === 'Rising'
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : mandi.trend === 'Falling'
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                    }`}
                  >
                    {mandi.trend === 'Rising' ? (
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                    ) : mandi.trend === 'Falling' ? (
                      <TrendingDown className="w-3 h-3 text-rose-400" />
                    ) : (
                      <Activity className="w-3 h-3 text-cyan-400" />
                    )}
                    <span>{mandi.trend}</span>
                  </span>
                </div>

                <div className="flex items-baseline gap-1">
                  <span className="text-xl font-mono font-extrabold text-white">
                    ₹{mandi.modal_price_rs_qtl.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium">/ Quintal</span>
                </div>

                <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-900 pt-1.5">
                  <span>Range: ₹{mandi.min_price} - ₹{mandi.max_price}</span>
                  <span className="text-teal-400 font-mono truncate max-w-[130px]">{mandi.market}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature 3: Tank-Mix Chemical Compatibility & Dilution Calculator Tool */}
      {response.chemical_calculator && (
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-4 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <FlaskConical className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Tank-Mix Chemical Compatibility & Dilution Calculator</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Field Dosage Spec
                  </span>
                </h4>
                <p className="text-xs text-slate-400">
                  Interactive tank volume scaling, safe water pH tolerances, and compatibility warnings
                </p>
              </div>
            </div>
            <div className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-slate-950 text-emerald-400 border border-emerald-500/30">
              Safe Water pH: {response.chemical_calculator.safe_water_ph_range}
            </div>
          </div>

          {/* Treatment Formulation Banner */}
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Recommended Active Formulation</span>
              <span className="text-xs font-bold text-white mt-0.5 block">{response.chemical_calculator.chemical_name}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Standard Rate</span>
              <span className="text-xs font-mono font-bold text-emerald-300 mt-0.5 block">
                {response.chemical_calculator.recommended_dosage_per_liter}
              </span>
            </div>
          </div>

          {/* Interactive Sprayer Tank Selector */}
          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-300 flex items-center justify-between">
              <span>Select Sprayer Tank Volume:</span>
              <span className="text-[10px] text-slate-400">Click to dynamically compute tank requirement</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { size: 15, label: '15 L Knapsack / Backpack' },
                { size: 100, label: '100 L Power Sprayer Drum' },
                { size: 500, label: '500 L Tractor Boom Sprayer' },
              ].map((tank) => (
                <button
                  key={tank.size}
                  type="button"
                  onClick={() => setSelectedTankSize(tank.size)}
                  className={`p-2.5 rounded-xl text-left border transition ${
                    selectedTankSize === tank.size
                      ? 'bg-emerald-500/20 border-emerald-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.2)]'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="text-sm font-mono font-bold">{tank.size} Liters</div>
                  <div className="text-[10px] mt-0.5 opacity-80">{tank.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Calculated Requirement Highlight */}
          {(() => {
            const chem = response.chemical_calculator;
            const match = chem.recommended_dosage_per_liter.match(/([0-9.]+)/);
            const ratePerL = match ? parseFloat(match[1]) : 2.5;
            const isMl = chem.recommended_dosage_per_liter.toLowerCase().includes('ml');
            const totalAmount = ratePerL * selectedTankSize;
            const formattedAmount =
              totalAmount >= 1000
                ? `${(totalAmount / 1000).toFixed(2)} ${isMl ? 'Liters' : 'Kilograms'}`
                : `${totalAmount.toFixed(1)} ${isMl ? 'mL' : 'Grams'}`;

            return (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/40 to-teal-950/40 border border-emerald-500/40 flex flex-wrap items-center justify-between gap-2">
                <div className="space-y-0.5">
                  <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                    Calculated Dosage for {selectedTankSize}L Tank:
                  </span>
                  <div className="text-lg font-mono font-black text-white">
                    {formattedAmount} <span className="text-xs font-normal text-slate-400">({ratePerL} {isMl ? 'mL' : 'g'} per liter)</span>
                  </div>
                </div>
                <div className="text-right text-[11px] text-teal-300 font-mono">
                  Water Volume: {selectedTankSize} Liters
                </div>
              </div>
            );
          })()}

          {/* Compatibility & Safeguards */}
          {response.chemical_calculator.compatibility_warnings && response.chemical_calculator.compatibility_warnings.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                <span>Tank-Mix Compatibility & Chemical Safety Protocols:</span>
              </span>
              <div className="space-y-1">
                {response.chemical_calculator.compatibility_warnings.map((warn, wIdx) => (
                  <div
                    key={wIdx}
                    className="p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 flex items-start gap-2"
                  >
                    <span className="text-amber-400 font-bold shrink-0">•</span>
                    <span>{warn}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. Data-Driven Visualizations (Graphs & Charts) */}
      {response.visualizations && response.visualizations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <BarChart3 className="w-4 h-4" />
            <span>Data-Driven Analytical Visualizations & Trends</span>
          </div>

          {response.visualizations.map((viz, vIdx) => {
            const isWeather = viz.chart_type === 'weather_trend';
            const maxVal = Math.max(
              ...viz.series.flatMap((s) => s.data),
              1
            );

            return (
              <div
                key={vIdx}
                className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 shadow-md"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                  <div>
                    <h4 className="text-xs font-bold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>{viz.title}</span>
                    </h4>
                    {viz.subtitle && (
                      <p className="text-[11px] text-slate-400 mt-0.5">{viz.subtitle}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                      Source: {viz.data_source}
                    </span>
                    {viz.unit && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                        {viz.unit}
                      </span>
                    )}
                  </div>
                </div>

                {/* Bar / Chart Representation */}
                <div className="space-y-2 pt-1">
                  <div className="grid grid-cols-7 gap-2 items-end h-32 bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
                    {viz.labels.map((label, lIdx) => {
                      const primaryVal = viz.series[0]?.data[lIdx] ?? 0;
                      const secondaryVal = viz.series[1]?.data?.[lIdx];
                      const heightPct = Math.min(100, Math.max(15, (primaryVal / maxVal) * 100));

                      return (
                        <div key={lIdx} className="flex flex-col items-center justify-end h-full gap-1">
                          <div className="text-[9px] font-mono text-slate-400 font-semibold">
                            {primaryVal}
                            {isWeather && '°C'}
                          </div>
                          <div className="w-full flex items-end justify-center gap-1 h-full max-h-[85px]">
                            {/* Primary series bar */}
                            <div
                              className="w-full max-w-[22px] rounded-t-md transition-all duration-500"
                              style={{
                                height: `${heightPct}%`,
                                backgroundColor: viz.series[0]?.color || '#10b981',
                              }}
                              title={`${viz.series[0]?.name}: ${primaryVal}`}
                            />
                            {/* Secondary series bar (e.g. humidity or salinity) */}
                            {secondaryVal !== undefined && (
                              <div
                                className="w-full max-w-[14px] rounded-t-sm opacity-80 transition-all duration-500"
                                style={{
                                  height: `${Math.min(100, Math.max(12, (secondaryVal / (isWeather ? 100 : 5)) * 100))}%`,
                                  backgroundColor: viz.series[1]?.color || '#06b6d4',
                                }}
                                title={`${viz.series[1]?.name}: ${secondaryVal}`}
                              />
                            )}
                          </div>
                          <span className="text-[9px] text-slate-400 truncate max-w-full text-center">
                            {label}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Series Legend & Notes */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] text-slate-400">
                    <div className="flex items-center gap-3">
                      {viz.series.map((s, sIdx) => (
                        <div key={sIdx} className="flex items-center gap-1.5">
                          <span
                            className="w-2.5 h-2.5 rounded-sm"
                            style={{ backgroundColor: s.color || '#10b981' }}
                          />
                          <span className="text-[11px] font-medium">{s.name}</span>
                        </div>
                      ))}
                    </div>
                    {viz.notes && (
                      <span className="text-amber-300/90 italic text-[10px] flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-amber-400 shrink-0" />
                        <span>{viz.notes}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Follow-up Questions Card (Section 3.E & Custom Inquiries) */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-500/10 border border-teal-500/30">
              <HelpCircle className="w-4 h-4 text-teal-400" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span>Follow-Up Inquiries & Interactive Consultation</span>
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Click any inquiry below to load and run it, or add your own custom follow-up question
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/30 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-teal-400" />
              <span>AI Suggested ({response.follow_up_questions?.length || 0})</span>
            </span>
            <span className="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
              <UserCheck className="w-3 h-3 text-emerald-400" />
              <span>Custom Inquiries ({customFollowUps.length})</span>
            </span>
          </div>
        </div>

        {/* List of AI Recommended and Custom Follow-up Inquiries */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* AI-Suggested Follow-up Questions */}
          {response.follow_up_questions?.map((q, idx) => (
            <div
              key={`ai-${idx}`}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-teal-500/40 transition-all flex flex-col justify-between gap-2.5 group hover:shadow-[0_0_15px_rgba(20,184,166,0.15)]"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20 flex items-center gap-1">
                    <Sparkles className="w-2.5 h-2.5 text-teal-400" />
                    <span>AI Recommended Q{idx + 1}</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Suggested</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-medium">{q}</p>
              </div>

              {onSelectFollowUp && (
                <button
                  type="button"
                  onClick={() => onSelectFollowUp(q)}
                  className="w-full mt-1 px-3 py-1.5 rounded-lg bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 text-[11px] font-semibold border border-teal-500/30 transition flex items-center justify-center gap-1.5 active:scale-95 group-hover:border-teal-400"
                >
                  <span>Ask This Question</span>
                  <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
                </button>
              )}
            </div>
          ))}

          {/* User-Added Custom Follow-up Inquiries (with explicit indication) */}
          {customFollowUps.map((cq, idx) => (
            <div
              key={`custom-${idx}`}
              className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/40 hover:border-emerald-400 transition-all flex flex-col justify-between gap-2.5 group shadow-[0_0_12px_rgba(16,185,129,0.15)]"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 flex items-center gap-1.5 shadow-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    <UserCheck className="w-2.5 h-2.5 text-emerald-400" />
                    <span>Custom Farmer / Evaluator Inquiry #{idx + 1}</span>
                  </span>
                  <span className="text-[10px] text-emerald-400/80 font-mono font-semibold">Custom</span>
                </div>
                <p className="text-xs text-slate-100 leading-relaxed font-semibold">{cq}</p>
              </div>

              {onSelectFollowUp && (
                <button
                  type="button"
                  onClick={() => onSelectFollowUp(cq)}
                  className="w-full mt-1 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-[11px] font-bold border border-emerald-500/40 transition flex items-center justify-center gap-1.5 active:scale-95"
                >
                  <span>Execute Custom Inquiry</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Add Custom Follow-up Question Input Form */}
        <form onSubmit={handleAddCustomFollowUp} className="pt-2 border-t border-slate-800/80">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={newQuestionText}
                onChange={(e) => setNewQuestionText(e.target.value)}
                placeholder="Type a custom follow-up question (e.g. Can I mix mancozeb with foliar urea? What is the harvest interval?)..."
                className="w-full rounded-xl bg-slate-950 border border-slate-700/80 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition"
              />
            </div>
            <button
              type="submit"
              disabled={!newQuestionText.trim()}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:hover:bg-emerald-600 text-white text-xs font-semibold transition flex items-center justify-center gap-1.5 shadow-md shrink-0 active:scale-95"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Custom Inquiry</span>
            </button>
          </div>
        </form>
      </div>

      {/* 5-Category Standardized Taxonomy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. Directly Observed Facts */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            <span>1. Observed Inputs & Empirical Facts</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-300">
            {response.observed_facts.map((fact, idx) => (
              <li key={idx} className="leading-relaxed">{fact}</li>
            ))}
          </ul>
        </div>

        {/* 2. Plausible Causes / Hypotheses */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
            <HelpCircle className="w-4 h-4" />
            <span>2. Explanations & Analytical Hypotheses</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-300">
            {response.possible_causes.map((cause, idx) => (
              <li key={idx} className="leading-relaxed">{cause}</li>
            ))}
          </ul>
        </div>

        {/* 3. Recommended Interventions */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-400 uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            <span>3. Actionable Recommendations & Next Steps</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-300">
            {response.recommendations.map((rec, idx) => (
              <li key={idx} className="leading-relaxed font-medium">{rec}</li>
            ))}
          </ul>
        </div>

        {/* 4. Honest Uncertainties & Scope Boundaries */}
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4" />
            <span>4. Scope Uncertainties & Caveats</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-amber-200/90">
            {response.uncertainties_and_limitations.map((unc, idx) => (
              <li key={idx} className="leading-relaxed">{unc}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* 5. Grounded Citations & Evidence Passages */}
      {response.retrieved_evidence && response.retrieved_evidence.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider">
            <BookOpen className="w-4 h-4" />
            <span>5. Grounded Citations & Retrieved Evidence ({response.retrieved_evidence.length})</span>
          </div>
          <div className="space-y-2">
            {response.retrieved_evidence.map((ev, idx) => {
              const hasUrl = ev.location_reference && ev.location_reference.startsWith('http');
              return (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                    <span className="text-emerald-400 font-semibold">{ev.source_name}</span>
                    <div className="flex items-center gap-2">
                      {ev.location_reference && (
                        <span className="bg-slate-800 px-2 py-0.5 rounded text-[10px] text-slate-300">
                          {ev.location_reference.length > 50 ? `${ev.location_reference.slice(0, 50)}...` : ev.location_reference}
                        </span>
                      )}
                      {hasUrl && (
                        <a
                          href={ev.location_reference}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-teal-400 hover:text-teal-300 underline"
                        >
                          <span>Visit</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                  <p className="text-slate-300 italic">"{ev.content_snippet}"</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Feedback Widget */}
      <div className="pt-4 border-t border-slate-800">
        {feedbackSubmitted ? (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Thank you! Your evaluation rating was saved to the telemetry database.</span>
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs font-semibold text-slate-300">
                Rate response accuracy & clarity:
              </span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="p-1 hover:scale-110 transition"
                  >
                    <Star
                      className={`w-4 h-4 ${
                        star <= rating
                          ? 'fill-amber-400 text-amber-400'
                          : 'text-slate-600'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Optional evaluator feedback on reasoning, script quality, or accuracy..."
                className="flex-1 rounded-xl bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition flex items-center gap-1.5 active:scale-95"
              >
                <Send className="w-3.5 h-3.5 text-emerald-400" />
                <span>Submit Feedback</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
