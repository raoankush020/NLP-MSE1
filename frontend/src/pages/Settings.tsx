import React, { useEffect, useState } from 'react';
import {
  Sliders,
  Save,
  CheckCircle2,
  Key,
  Cpu,
  Layers,
  Sparkles,
  Info,
  Lock
} from 'lucide-react';
import { settingsApi } from '../services/api';
import { UserSettings } from '../types';

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>({
    llm_model: 'extractive-grounded',
    temperature: 0.2,
    top_k: 4,
    chunk_size: 500,
    chunk_overlap: 50,
    embedding_model: 'all-MiniLM-L6-v2',
    has_custom_api_key: false,
  });
  const [customKey, setCustomKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    settingsApi
      .getSettings()
      .then((res) => setSettings(res))
      .catch((err) => console.error('Failed to load settings:', err))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);

    try {
      const payload: any = { ...settings };
      if (customKey.trim()) {
        payload.custom_api_key = customKey.trim();
      }
      const updated = await settingsApi.updateSettings(payload);
      setSettings(updated);
      setCustomKey('');
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert('Error updating configuration.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-slate-400">Loading settings...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System & Pipeline Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Tune retrieval depth, chunking segmentation, and LLM synthesis engines
        </p>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" />
          <span>Configuration saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="glass-card p-6 rounded-2xl border border-slate-800 space-y-6 shadow-xl">
        {/* LLM Engine Selection */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>LLM Synthesis Engine</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1.5">
              Generation Model
            </label>
            <select
              value={settings.llm_model}
              onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl py-2.5 px-3 text-sm text-slate-100 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="extractive-grounded">
                Grounded Extractive RAG (Built-in Zero-Latency Engine, 100% Deterministic)
              </option>
              <option value="gemini">Google Gemini 1.5 Flash (via API Key)</option>
              <option value="openai">OpenAI GPT-3.5 Turbo / GPT-4o (via API Key)</option>
            </select>
          </div>

          {/* Custom API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-slate-400" />
                <span>Custom API Key (Optional)</span>
              </label>
              {settings.has_custom_api_key && (
                <span className="text-[11px] text-emerald-400 font-medium">● Key configured on server</span>
              )}
            </div>
            <input
              type="password"
              value={customKey}
              onChange={(e) => setCustomKey(e.target.value)}
              placeholder={settings.has_custom_api_key ? '••••••••••••••••••••••••' : 'Enter Gemini or OpenAI API Key'}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl py-2.5 px-3 text-sm text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:outline-none font-mono"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              API keys are encrypted and stored safely on the backend. They are never exposed in browser network responses.
            </p>
          </div>
        </div>

        {/* Temperature & Retrieval Depth */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <span>Generation & Retrieval Parameters</span>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate-300">Temperature: {settings.temperature}</label>
              <span className="text-xs font-mono text-slate-400">0.0 (Strict) - 1.0 (Creative)</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={settings.temperature}
              onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
              className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate-300">Top-K Retrieved Chunks: {settings.top_k}</label>
              <span className="text-xs font-mono text-slate-400">Context Chunks</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={settings.top_k}
              onChange={(e) => setSettings({ ...settings, top_k: parseInt(e.target.value, 10) })}
              className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Ingestion & Embedding Defaults */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>Document Ingestion Defaults</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Chunk Size</label>
              <input
                type="number"
                min="100"
                max="2000"
                value={settings.chunk_size}
                onChange={(e) => setSettings({ ...settings, chunk_size: parseInt(e.target.value, 10) || 500 })}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl py-2 px-3 text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Chunk Overlap</label>
              <input
                type="number"
                min="0"
                max="500"
                value={settings.chunk_overlap}
                onChange={(e) => setSettings({ ...settings, chunk_overlap: parseInt(e.target.value, 10) || 50 })}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl py-2 px-3 text-sm text-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Embedding Model</label>
            <input
              type="text"
              value={settings.embedding_model}
              onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl py-2 px-3 text-sm text-slate-100 font-mono"
            />
          </div>
        </div>

        {/* Submit */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-600/20 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
