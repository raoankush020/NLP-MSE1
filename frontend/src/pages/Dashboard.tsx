import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Files,
  MessageSquare,
  ClipboardCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ShieldCheck,
  RefreshCw,
  ArrowUpRight,
  TrendingUp,
  BarChart2
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar
} from 'recharts';
import { dashboardApi } from '../services/api';
import { DashboardStats, DashboardCharts } from '../types';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [statsData, chartsData] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getCharts()
      ]);
      setStats(statsData);
      setCharts(chartsData);
    } catch (err: any) {
      console.error('Error loading dashboard metrics:', err);
      setError('Failed to fetch real-time dashboard analytics. Please ensure backend is running.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-8 w-48 bg-slate-800 rounded-lg animate-pulse" />
          <div className="h-9 w-24 bg-slate-800 rounded-lg animate-pulse" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
          <div className="h-72 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Documents',
      value: stats?.total_documents ?? 0,
      icon: Files,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20',
      link: '/documents'
    },
    {
      title: 'Total Queries',
      value: stats?.total_queries ?? 0,
      icon: MessageSquare,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10',
      border: 'border-indigo-500/20',
      link: '/chat'
    },
    {
      title: 'Total Evaluations',
      value: stats?.total_evaluations ?? 0,
      icon: ClipboardCheck,
      color: 'text-teal-400',
      bg: 'bg-teal-500/10',
      border: 'border-teal-500/20',
      link: '/history'
    },
    {
      title: 'Grounded Answers',
      value: stats?.grounded_answers ?? 0,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      badge: stats && stats.total_evaluations > 0 ? `${Math.round((stats.grounded_answers / stats.total_evaluations) * 100)}%` : undefined
    },
    {
      title: 'Hallucinated Answers',
      value: stats?.hallucinated_answers ?? 0,
      icon: AlertTriangle,
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/20',
      badge: stats && stats.total_evaluations > 0 ? `${Math.round((stats.hallucinated_answers / stats.total_evaluations) * 100)}%` : undefined
    },
    {
      title: 'Avg Support Score',
      value: stats ? `${Math.round(stats.average_support_score * 100)}%` : '0%',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      subtitle: 'Higher is better (factual grounding)'
    },
    {
      title: 'Avg Hallucination Score',
      value: stats ? `${Math.round(stats.average_hallucination_score * 100)}%` : '0%',
      icon: Flame,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      subtitle: 'Lower is better'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System Analytics & Health</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time factual verification and hallucination detection telemetry across your ingested documents
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Stats</span>
          </button>
          <Link
            to="/chat"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-md shadow-emerald-600/20"
          >
            <span>Ask a Question</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchData} className="underline text-xs hover:text-red-300">Try Again</button>
        </div>
      )}

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <div
              key={idx}
              className={`glass-card p-5 rounded-xl border ${c.border} flex flex-col justify-between relative overflow-hidden transition-transform hover:-translate-y-0.5`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{c.title}</span>
                <div className={`p-2 rounded-lg ${c.bg}`}>
                  <Icon className={`w-4 h-4 ${c.color}`} />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">{c.value}</span>
                {c.badge && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c.bg} ${c.color}`}>
                    {c.badge}
                  </span>
                )}
              </div>
              {c.subtitle && <p className="text-[11px] text-slate-400 mt-1">{c.subtitle}</p>}
              {c.link && (
                <Link to={c.link} className="text-[11px] text-emerald-400 hover:text-emerald-300 mt-2 flex items-center gap-1">
                  <span>View Details</span>
                  <ArrowUpRight className="w-3 h-3" />
                </Link>
              )}
            </div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grounded vs Hallucinated Donut */}
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Grounded vs Hallucinated Answers</h3>
            <span className="text-xs text-slate-400">Total Evaluations: {stats?.total_evaluations ?? 0}</span>
          </div>
          <div className="h-64 w-full">
            {stats && stats.total_evaluations > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts?.grounded_vs_hallucinated || []}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                  >
                    {(charts?.grounded_vs_hallucinated || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ color: '#cbd5e1', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs gap-2">
                <BarChart2 className="w-8 h-8 text-slate-600" />
                <span>No evaluation queries run yet. Start asking questions in RAG Chat!</span>
              </div>
            )}
          </div>
        </div>

        {/* Hallucination Severity Breakdown */}
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Hallucination Severity Tiers</h3>
            <span className="text-xs text-slate-400">Classification Tiers</span>
          </div>
          <div className="h-64 w-full">
            {stats && stats.total_evaluations > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts?.hallucination_types || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  />
                  <Bar dataKey="value" name="Evaluations" radius={[4, 4, 0, 0]}>
                    {(charts?.hallucination_types || []).map((entry, index) => (
                      <Cell key={`cell-type-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs gap-2">
                <BarChart2 className="w-8 h-8 text-slate-600" />
                <span>No classification data available yet.</span>
              </div>
            )}
          </div>
        </div>

        {/* Queries Over Time */}
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Queries Activity (Last 7 Days)</h3>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts?.queries_over_time || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Area type="monotone" dataKey="queries" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#queryGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Support Score Distribution */}
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Support Score Distribution</h3>
            <span className="text-xs text-slate-400">Score Bins</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts?.support_score_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="range" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="count" name="Evaluations" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
