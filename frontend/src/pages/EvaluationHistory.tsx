import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  History,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldAlert,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { evaluationApi } from '../services/api';
import { EvaluationListItem } from '../types';

export const EvaluationHistory: React.FC = () => {
  const [evaluations, setEvaluations] = useState<EvaluationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const navigate = useNavigate();

  const fetchEvaluations = async () => {
    try {
      setLoading(true);
      const data = await evaluationApi.getEvaluations(search, statusFilter);
      setEvaluations(data);
    } catch (err) {
      console.error('Failed to load evaluation history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluations();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEvaluations();
  };

  const sortedList = [...evaluations].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
  });

  const totalPages = Math.ceil(sortedList.length / pageSize) || 1;
  const paginatedList = sortedList.slice((page - 1) * pageSize, page * pageSize);

  const getStatusBadge = (classification: string) => {
    switch (classification) {
      case 'NOT_HALLUCINATED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>Grounded</span>
          </span>
        );
      case 'LOW_HALLUCINATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <span>Low</span>
          </span>
        );
      case 'MEDIUM_HALLUCINATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Flame className="w-3 h-3" />
            <span>Medium</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
            <ShieldAlert className="w-3 h-3" />
            <span>High</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Evaluation History & Audit Log</h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical record of all RAG answer evaluations and verified claim breakdown scores
          </p>
        </div>
        <button
          onClick={fetchEvaluations}
          className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl transition-colors self-start sm:self-auto"
          title="Refresh history"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Search and Filters */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by question..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </form>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-slate-900 border border-slate-700/80 rounded-xl text-xs text-slate-200 py-2 px-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="NOT_HALLUCINATED">Not Hallucinated</option>
              <option value="LOW_HALLUCINATION">Low Hallucination</option>
              <option value="MEDIUM_HALLUCINATION">Medium Hallucination</option>
              <option value="HIGH_HALLUCINATION">High Hallucination</option>
            </select>
          </div>

          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-xs text-slate-300 transition-colors"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">User Question</th>
                <th className="py-3.5 px-4">Support Score</th>
                <th className="py-3.5 px-4">Hallucination Score</th>
                <th className="py-3.5 px-4">Classification</th>
                <th className="py-3.5 px-4 text-right">Drill-down</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading evaluations...
                  </td>
                </tr>
              ) : paginatedList.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-500">
                    <History className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                    <p className="text-sm">No evaluation records match your query.</p>
                  </td>
                </tr>
              ) : (
                paginatedList.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => navigate(`/analysis/${item.id}`)}
                    className="hover:bg-slate-900/60 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleDateString()}{' '}
                      <span className="text-slate-500">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200 max-w-sm truncate">
                      {item.question}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                      {Math.round(item.support_score * 100)}%
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                      {Math.round(item.hallucination_score * 100)}%
                    </td>
                    <td className="py-3.5 px-4">{getStatusBadge(item.classification)}</td>
                    <td className="py-3.5 px-4 text-right text-slate-400 hover:text-emerald-400">
                      <ChevronRight className="w-4 h-4 ml-auto" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-between text-xs text-slate-400">
          <span>
            Page {page} of {totalPages} ({sortedList.length} total records)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
