import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Files,
  UploadCloud,
  Search,
  RefreshCw,
  Trash2,
  RotateCcw,
  Eye,
  FileText,
  AlertCircle,
  CheckCircle2,
  Clock,
  X,
  Layers
} from 'lucide-react';
import { documentApi } from '../services/api';
import { DocumentItem } from '../types';

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = async () => {
    try {
      setError(null);
      const data = await documentApi.getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError('Failed to fetch documents from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}" and all its vector index chunks?`)) {
      return;
    }
    try {
      setActionLoading(id);
      await documentApi.deleteDocument(id);
      setDocuments(documents.filter((d) => d.id !== id));
      if (selectedDoc?.id === id) setSelectedDoc(null);
    } catch (err: any) {
      alert('Error deleting document: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      setActionLoading(id);
      const updated = await documentApi.reprocessDocument(id);
      setDocuments(documents.map((d) => (d.id === id ? updated : d)));
    } catch (err: any) {
      alert('Error reprocessing document: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewDetails = async (id: string) => {
    try {
      setModalLoading(true);
      const detail = await documentApi.getDocumentDetail(id);
      setSelectedDoc(detail);
    } catch (err: any) {
      alert('Failed to load document chunk details.');
    } finally {
      setModalLoading(false);
    }
  };

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'INDEXED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Indexed</span>
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Clock className="w-3.5 h-3.5 animate-spin" />
            <span>Processing</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400">
            <span>Pending</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Document Repository</h1>
          <p className="text-sm text-slate-400 mt-1">
            Uploaded corpus indexed for RAG context retrieval and factual ground-truth verification
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDocs}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl transition-colors"
            title="Refresh list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/documents/upload"
            className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/20 transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Document</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Search & Stats Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents by name..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-200">{filteredDocs.length}</span> of{' '}
          <span className="font-semibold text-slate-200">{documents.length}</span> documents
        </div>
      </div>

      {/* Documents Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3.5 px-4">File Name</th>
                <th className="py-3.5 px-4">Type</th>
                <th className="py-3.5 px-4">Upload Date</th>
                <th className="py-3.5 px-4">Chunks</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <div className="inline-flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                      <span>Loading documents...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center">
                    <div className="max-w-xs mx-auto flex flex-col items-center">
                      <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-600 mb-3">
                        <Files className="w-6 h-6" />
                      </div>
                      <p className="text-slate-300 font-medium text-sm">No documents found</p>
                      <p className="text-slate-500 text-xs mt-1">
                        {search ? 'No matches for your search term.' : 'Upload PDF, DOCX, or TXT documents to start.'}
                      </p>
                      {!search && (
                        <Link
                          to="/documents/upload"
                          className="mt-4 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-semibold transition-colors"
                        >
                          Upload First Document
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-800 text-emerald-400">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="truncate max-w-xs sm:max-w-md">
                          <p className="font-medium text-slate-200 truncate">{doc.filename}</p>
                          <p className="text-xs text-slate-500 font-mono">
                            {(doc.file_size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono uppercase font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()} {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <Layers className="w-3.5 h-3.5 text-slate-500" />
                        <span>{doc.chunk_count}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">{getStatusBadge(doc.status)}</td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleViewDetails(doc.id)}
                          title="View Chunks"
                          className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-slate-800 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleReprocess(doc.id)}
                          disabled={actionLoading === doc.id}
                          title="Reprocess Document"
                          className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-40"
                        >
                          <RotateCcw className={`w-4 h-4 ${actionLoading === doc.id ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          disabled={actionLoading === doc.id}
                          title="Delete Document"
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-40"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Chunk Details Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-card w-full max-w-3xl max-h-[85vh] rounded-2xl border border-slate-800 flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-emerald-400" />
                  <span>{selectedDoc.filename}</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Indexed into {selectedDoc.chunks?.length || selectedDoc.chunk_count} vector chunks
                </p>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Chunks list */}
            <div className="p-6 overflow-y-auto space-y-4 divide-y divide-slate-800/60">
              {modalLoading ? (
                <div className="py-12 text-center text-slate-400">Loading chunk representations...</div>
              ) : selectedDoc.chunks && selectedDoc.chunks.length > 0 ? (
                selectedDoc.chunks.map((chunk, idx) => (
                  <div key={chunk.id} className="pt-4 first:pt-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-emerald-400 font-mono">
                        Chunk #{chunk.chunk_index} (Page {chunk.page_number})
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">ID: {chunk.id.slice(0, 8)}...</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">
                      {chunk.content}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-slate-400 text-sm">
                  No individual chunks found for this document.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
