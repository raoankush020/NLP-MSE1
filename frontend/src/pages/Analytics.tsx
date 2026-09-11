import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart as PieIcon,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw
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

export const Analytics: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [s, c] = await Promise.all([dashboardApi.getStats(), dashboardApi.getCharts()]);
      setStats(s);
      setCharts(c);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Hallucination & Grounding Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical distribution of factual claim classifications and temporal grounding metrics
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Total Evaluations</span>
          <p className="text-2xl font-bold text-white mt-1">{stats?.total_evaluations ?? 0}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-emerald-500/20">
          <span className="text-[11px] font-semibold text-emerald-400 uppercase">Grounded Answers</span>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{stats?.grounded_answers ?? 0}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-red-500/20">
          <span className="text-[11px] font-semibold text-red-400 uppercase">Hallucinated Answers</span>
          <p className="text-2xl font-bold text-red-400 mt-1">{stats?.hallucinated_answers ?? 0}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-teal-500/20">
          <span className="text-[11px] font-semibold text-teal-400 uppercase">Avg Support Score</span>
          <p className="text-2xl font-bold text-teal-400 mt-1">
            {stats ? `${Math.round(stats.average_support_score * 100)}%` : '0%'}
          </p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-amber-500/20">
          <span className="text-[11px] font-semibold text-amber-400 uppercase">Avg Hallucination</span>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            {stats ? `${Math.round(stats.average_hallucination_score * 100)}%` : '0%'}
          </p>
        </div>
      </div>

      {/* Deep Dive Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Claim Classification Breakdown */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Claim-Level Classification Distribution</h3>
            <span className="text-xs text-slate-400">All Evaluated Claims</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts?.claim_classifications || []}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {(charts?.claim_classifications || []).map((entry, index) => (
                    <Cell key={`claim-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hallucination Rate Progression */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Cumulative Hallucination Rate</h3>
            <span className="text-xs text-slate-400">% Hallucinated Queries</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts?.hallucination_rates || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="rateGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Area type="monotone" dataKey="rate" name="Hallucination %" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#rateGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
