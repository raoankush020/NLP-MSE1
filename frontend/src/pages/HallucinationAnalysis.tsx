import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Flame,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowLeft,
  FileText,
  Info,
  Sparkles,
  Layers
} from 'lucide-react';
import { evaluationApi } from '../services/api';
import { EvaluationDetail, ClaimItem, ClaimClassification } from '../types';

export const HallucinationAnalysis: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<EvaluationDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClaimIndex, setSelectedClaimIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    evaluationApi
      .getEvaluationDetail(id)
      .then((res) => {
        setData(res);
        if (res.claims && res.claims.length > 0) {
          setSelectedClaimIndex(0);
        }
      })
      .catch((err) => {
        console.error('Error fetching evaluation analysis:', err);
        setError('Failed to load evaluation details. Record may not exist.');
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
        <p className="text-sm text-slate-400 font-medium">Extracting claims and analyzing evidence...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-red-500/10 text-red-400 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white">Evaluation Not Found</h2>
        <p className="text-xs text-slate-400">{error || 'Unable to retrieve evaluation analysis.'}</p>
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to History</span>
        </Link>
      </div>
    );
  }

  const supportPct = Math.round(data.support_score * 100);
  const hallPct = Math.round(data.hallucination_score * 100);

  const getStatusBadge = (classification: string) => {
    switch (classification) {
      case 'NOT_HALLUCINATED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-4 h-4" />
            <span>NOT HALLUCINATED (Ground-truth Verified)</span>
          </span>
        );
      case 'LOW_HALLUCINATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
            <ShieldCheck className="w-4 h-4" />
            <span>LOW HALLUCINATION</span>
          </span>
        );
      case 'MEDIUM_HALLUCINATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Flame className="w-4 h-4" />
            <span>MEDIUM HALLUCINATION</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30">
            <ShieldAlert className="w-4 h-4" />
            <span>HIGH HALLUCINATION (Severe Incoherence)</span>
          </span>
        );
    }
  };

  const getClaimStyle = (classification: ClaimClassification) => {
    switch (classification) {
      case 'SUPPORTED':
        return {
          bg: 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          icon: CheckCircle2,
          label: 'SUPPORTED',
          border: 'border-emerald-500/40',
        };
      case 'PARTIALLY_SUPPORTED':
        return {
          bg: 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border-amber-500/30',
          badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          icon: AlertTriangle,
          label: 'PARTIALLY SUPPORTED',
          border: 'border-amber-500/40',
        };
      case 'CONTRADICTED':
        return {
          bg: 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border-purple-500/30',
          badge: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
          icon: XCircle,
          label: 'CONTRADICTED',
          border: 'border-purple-500/40',
        };
      default:
        return {
          bg: 'bg-red-500/10 hover:bg-red-500/20 text-red-300 border-red-500/30',
          badge: 'bg-red-500/20 text-red-400 border-red-500/30',
          icon: ShieldAlert,
          label: 'UNSUPPORTED (HALLUCINATION)',
          border: 'border-red-500/40',
        };
    }
  };

  const selectedClaim =
    selectedClaimIndex !== null && data.claims[selectedClaimIndex]
      ? data.claims[selectedClaimIndex]
      : null;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Audit Log</span>
        </Link>
        <span className="text-xs text-slate-500 font-mono">Evaluation ID: {data.id}</span>
      </div>

      {/* Summary Banner Card */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Evaluation Verdict</span>
            <div className="mt-1.5 flex items-center gap-3">{getStatusBadge(data.classification)}</div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Support Score</span>
              <p className="text-2xl font-black text-emerald-400 tracking-tight">{supportPct}%</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-right">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Hallucination Score</span>
              <p className="text-2xl font-black text-amber-400 tracking-tight">{hallPct}%</p>
            </div>
          </div>
        </div>

        {/* Question */}
        <div>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">User Question</span>
          <p className="text-base font-semibold text-white mt-1">"{data.question}"</p>
        </div>
      </div>

      {/* Interactive Answer Sentence Highlighting */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">Answer Sentence Grounding Map</h3>
          </div>
          <span className="text-xs text-slate-400">Click any sentence below to inspect evidence</span>
        </div>

        <p className="text-xs text-slate-400">
          Every sentence is color-coded based on its factual alignment with the retrieved context:
        </p>

        {/* Legend */}
        <div className="flex flex-wrap gap-2 text-[11px] pt-1 pb-2">
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            ● Supported (1.0)
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
            ● Partially Supported (0.5)
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
            ● Hallucinated / Unsupported (0.0)
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
            ● Contradicted (0.0)
          </span>
        </div>

        {/* Highlighted text container */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 text-sm leading-relaxed">
          {data.claims.map((c, idx) => {
            const style = getClaimStyle(c.classification);
            const isSelected = selectedClaimIndex === idx;
            return (
              <span
                key={idx}
                onClick={() => setSelectedClaimIndex(idx)}
                className={`inline-block mx-0.5 my-1 px-2 py-0.5 rounded-md cursor-pointer transition-all border ${style.bg} ${
                  isSelected ? `ring-2 ring-emerald-400 font-medium ${style.border}` : 'border-transparent'
                }`}
                title={`Click to view claim #${idx + 1}`}
              >
                {c.claim}{' '}
              </span>
            );
          })}
        </div>
      </div>

      {/* Selected Claim Inspector Drill-down */}
      {selectedClaim && (
        <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4 animate-in fade-in">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">
                Selected Claim #{selectedClaimIndex! + 1} Drill-down
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getClaimStyle(selectedClaim.classification).badge}`}>
                {getClaimStyle(selectedClaim.classification).label}
              </span>
              <span className="text-xs font-mono text-slate-400">Score: {selectedClaim.score.toFixed(1)}</span>
            </div>
          </div>

          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Claim Text</span>
            <p className="text-sm font-medium text-slate-100 mt-1 bg-slate-900 p-3 rounded-xl border border-slate-800">
              "{selectedClaim.claim}"
            </p>
          </div>

          {/* Evidence or Contradiction */}
          {selectedClaim.classification === 'CONTRADICTED' ? (
            <div>
              <span className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                <XCircle className="w-3.5 h-3.5" />
                Conflicting Context in Ingested Document
              </span>
              <div className="mt-1 p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-xs font-mono leading-relaxed">
                {selectedClaim.conflicting_text || 'Contradicting statement detected in context.'}
              </div>
            </div>
          ) : (
            <div>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Supporting Context Evidence
              </span>
              <div className="mt-1 p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono leading-relaxed">
                {selectedClaim.evidence ? `"${selectedClaim.evidence}"` : 'No supporting evidence found in context.'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Complete Claims Breakdown Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl space-y-4 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">All Decomposed Factual Claims ({data.claims.length})</h3>
          </div>
          <span className="text-xs text-slate-400">Strictly verified against retrieved context</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Factual Claim</th>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3">Score</th>
                <th className="py-2.5 px-3">Evidence / Conflict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {data.claims.map((claim, idx) => {
                const style = getClaimStyle(claim.classification);
                return (
                  <tr
                    key={idx}
                    onClick={() => setSelectedClaimIndex(idx)}
                    className={`cursor-pointer hover:bg-slate-900/60 transition-colors ${
                      selectedClaimIndex === idx ? 'bg-slate-900/80' : ''
                    }`}
                  >
                    <td className="py-3 px-3 font-mono text-slate-500">{idx + 1}</td>
                    <td className="py-3 px-3 font-medium text-slate-200 max-w-xs">{claim.claim}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${style.badge}`}>
                        {claim.classification}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-semibold text-slate-300">
                      {claim.score.toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px] max-w-md truncate">
                      {claim.classification === 'CONTRADICTED'
                        ? claim.conflicting_text
                        : claim.evidence || 'No supporting evidence found.'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Retrieved Context Chunks */}
      <div className="glass-card rounded-2xl border border-slate-800 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white">Retrieved Context Ground-Truth ({data.retrieved_context.length} Chunks)</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.retrieved_context.map((ctx, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="font-semibold text-slate-200">Source: {ctx.source}</span>
                <span className="font-mono text-emerald-400">Similarity: {ctx.similarity.toFixed(2)}</span>
              </div>
              <p className="text-slate-300 font-mono text-[11px] leading-relaxed bg-slate-950 p-2.5 rounded border border-slate-800/60 whitespace-pre-wrap">
                "{ctx.text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
