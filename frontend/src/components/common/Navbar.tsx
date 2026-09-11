import React from 'react';
import { useLocation } from 'react-router-dom';
import { Activity, Bell, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const routeTitles: Record<string, string> = {
  '/dashboard': 'System Overview & Metrics',
  '/documents': 'Document Repository',
  '/documents/upload': 'Ingest New Documents',
  '/chat': 'RAG Assistant & Evaluation',
  '/history': 'Audit Log & History',
  '/analytics': 'In-Depth Hallucination Analytics',
  '/settings': 'Pipeline & Model Configuration',
};

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();

  // Match title or subpath
  let title = 'Dashboard';
  for (const [path, t] of Object.entries(routeTitles)) {
    if (location.pathname.startsWith(path)) {
      title = t;
      break;
    }
  }
  if (location.pathname.startsWith('/analysis/')) {
    title = 'Factual Claim Verification Drill-down';
  }

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-lg font-semibold text-white tracking-tight">{title}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400">
          <Activity className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
          <span>Vector & Classifier Engine Online</span>
        </div>

        <div className="h-4 w-px bg-slate-800 hidden sm:block" />

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 hidden md:inline">Logged in as</span>
          <span className="text-xs font-medium text-slate-200 bg-slate-800 px-2.5 py-1 rounded-md border border-slate-700">
            {user?.email}
          </span>
        </div>
      </div>
    </header>
  );
};
