import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Send,
  Bot,
  User as UserIcon,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  Flame,
  FileText,
  Sparkles,
  ExternalLink,
  Layers,
  ArrowRight
} from 'lucide-react';
import { ragApi, documentApi } from '../services/api';
import { QueryResult, DocumentItem } from '../types';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  result?: QueryResult;
  timestamp: string;
}

export const RagChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('ALL');
  const [expandedContexts, setExpandedContexts] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load available documents for filter
    documentApi.getDocuments().then(setDocuments).catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleContextExpand = (msgId: string) => {
    setExpandedContexts((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputValue.trim();
    if (!query || loading) return;

    const userMsgId = Date.now().toString();
    const newMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputValue('');
    setLoading(true);

    try {
      const docIds = selectedDocId === 'ALL' ? undefined : [selectedDocId];
      const result = await ragApi.query(query, docIds);

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: result.answer,
        result: result,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || 'Failed to process question. Please verify backend is running.';
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: `Error: ${errMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusPill = (hallucination: QueryResult['hallucination']) => {
    const isHallucinated = hallucination.hallucinated;
    const supportPct = Math.round(hallucination.support_score * 100);
    const hallPct = Math.round(hallucination.hallucination_score * 100);

    if (hallucination.classification === 'NOT_HALLUCINATED') {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Grounded (Support: {supportPct}%)</span>
        </div>
      );
    } else if (hallucination.classification === 'LOW_HALLUCINATION') {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Low Hallucination ({supportPct}% Supported)</span>
        </div>
      );
    } else if (hallucination.classification === 'MEDIUM_HALLUCINATION') {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Flame className="w-3.5 h-3.5" />
          <span>Medium Hallucination ({hallPct}% Unverified)</span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>High Hallucination ({hallPct}% Unverified)</span>
        </div>
      );
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-5xl mx-auto">
      {/* Top Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">RAG Interactive Assistant</h1>
          <p className="text-xs text-slate-400">Contextual question answering with automated factual claim verification</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Query Scope:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="ALL">Entire Indexed Repository ({documents.length} docs)</option>
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.chunk_count} chunks)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4 shadow-lg">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white">Ask anything about your documents</h3>
            <p className="text-xs text-slate-400 max-w-md mt-1 mb-6">
              Answers will be generated exclusively from your retrieved chunks and audited sentence-by-sentence for factual hallucinations.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {[
                "What are the key conclusions in the uploaded document?",
                "Summarize the main methodology and findings.",
                "Who was involved and what dates are mentioned?",
              ].map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInputValue(sample);
                  }}
                  className="text-xs px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors"
                >
                  "{sample}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-800 text-emerald-400 flex items-center justify-center shrink-0 shadow-sm">
                  <Bot className="w-5 h-5" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-5 ${
                  msg.sender === 'user'
                    ? 'bg-emerald-600 text-white rounded-br-none shadow-md shadow-emerald-600/20'
                    : 'glass-card border border-slate-800 text-slate-100 rounded-bl-none shadow-xl space-y-4'
                }`}
              >
                {/* Message Header */}
                <div className="flex items-center justify-between gap-4 mb-1">
                  <span className={`text-[11px] font-bold uppercase tracking-wider ${msg.sender === 'user' ? 'text-emerald-200' : 'text-slate-400'}`}>
                    {msg.sender === 'user' ? 'User Question' : 'Generated Answer'}
                  </span>
                  <span className={`text-[10px] ${msg.sender === 'user' ? 'text-emerald-200' : 'text-slate-500'}`}>
                    {msg.timestamp}
                  </span>
                </div>

                {/* Answer Text */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</div>

                {/* Assistant Extended Telemetry: Retrieved Context & Hallucination Summary */}
                {msg.result && (
                  <div className="pt-4 border-t border-slate-800 space-y-3">
                    {/* Hallucination Badge & Analysis Button */}
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {getStatusPill(msg.result.hallucination)}
                      <Link
                        to={`/analysis/${msg.result.evaluation_id || msg.result.query_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20 transition-colors"
                      >
                        <span>View Claim Drill-down</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>

                    {/* Expandable Retrieved Context Cards */}
                    <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 overflow-hidden">
                      <button
                        onClick={() => toggleContextExpand(msg.id)}
                        className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-medium text-slate-300 hover:bg-slate-800/40 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Layers className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Retrieved Context ({msg.result.retrieved_context.length} Chunks)</span>
                        </div>
                        {expandedContexts[msg.id] ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </button>

                      {expandedContexts[msg.id] && (
                        <div className="p-3 space-y-2.5 border-t border-slate-800 bg-slate-950/60">
                          {msg.result.retrieved_context.map((ctx, idx) => (
                            <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1.5">
                              <div className="flex items-center justify-between text-[11px] text-slate-400">
                                <span className="font-semibold text-slate-200">Source: {ctx.source}</span>
                                <div className="flex items-center gap-3">
                                  <span>Page: {ctx.page}</span>
                                  <span className="font-mono text-emerald-400">
                                    Similarity: {ctx.similarity.toFixed(2)}
                                  </span>
                                </div>
                              </div>
                              <p className="text-slate-300 font-mono text-[11px] leading-relaxed bg-slate-950/80 p-2 rounded border border-slate-800/50">
                                "{ctx.text}"
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 text-emerald-400 flex items-center justify-center shrink-0 shadow-sm">
                  <UserIcon className="w-5 h-5" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3.5 justify-start">
            <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-800 text-emerald-400 flex items-center justify-center shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div className="glass-card rounded-2xl rounded-bl-none p-4 flex items-center gap-2 text-xs text-slate-400 border border-slate-800">
              <div className="w-4 h-4 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
              <span>Retrieving chunks & verifying claims against context...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input Box */}
      <div className="pt-3 border-t border-slate-800">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question grounded in your documents..."
            disabled={loading}
            className="w-full pl-5 pr-14 py-3.5 bg-slate-900 border border-slate-800 rounded-2xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all shadow-xl"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            className="absolute right-2 p-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-emerald-600/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
