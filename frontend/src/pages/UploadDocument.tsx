import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Sliders,
  X,
  FileCheck
} from 'lucide-react';
import { documentApi } from '../services/api';
import { DocumentItem } from '../types';

export const UploadDocument: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [chunkSize, setChunkSize] = useState<number>(500);
  const [chunkOverlap, setChunkOverlap] = useState<number>(50);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploading, setUploading] = useState<boolean>(false);
  const [processingStatus, setProcessingStatus] = useState<'IDLE' | 'UPLOADING' | 'PROCESSING' | 'INDEXED' | 'FAILED'>('IDLE');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdDoc, setCreatedDoc] = useState<DocumentItem | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    const validExts = ['pdf', 'docx', 'txt', 'md', 'markdown'];
    if (!ext || !validExts.includes(ext)) {
      setErrorMessage(`Invalid file type .${ext}. Please upload PDF, DOCX, TXT, or MD.`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setErrorMessage('File size exceeds maximum allowed limit of 25MB.');
      return;
    }
    setErrorMessage(null);
    setSelectedFile(file);
    setProcessingStatus('IDLE');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setErrorMessage(null);
      setProcessingStatus('UPLOADING');
      setUploadProgress(10);

      const doc = await documentApi.uploadDocument(
        selectedFile,
        chunkSize,
        chunkOverlap,
        (percent) => {
          setUploadProgress(percent);
          if (percent >= 100) {
            setProcessingStatus('PROCESSING');
          }
        }
      );

      setProcessingStatus('INDEXED');
      setCreatedDoc(doc);
      setUploadProgress(100);
    } catch (err: any) {
      setProcessingStatus('FAILED');
      const detail = err.response?.data?.detail || err.message || 'Failed to upload document.';
      setErrorMessage(detail);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Ingest & Vectorize Document</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload reference text, research papers, or knowledge base articles. They are parsed into chunks, embedded, and indexed in the vector database.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Success Banner */}
      {processingStatus === 'INDEXED' && createdDoc && (
        <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="font-semibold text-white text-sm">Document Indexed Successfully!</p>
              <p className="text-xs text-emerald-300 mt-0.5">
                "{createdDoc.filename}" split into {createdDoc.chunk_count} chunks with semantic vector representations.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <Link
              to="/documents"
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              View Repository
            </Link>
            <Link
              to="/chat"
              className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-colors"
            >
              <span>Test in Chat</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Dropzone (2 Cols) */}
        <div className="md:col-span-2 space-y-4">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`glass-card border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[260px] ${
              dragActive
                ? 'border-emerald-500 bg-emerald-500/10 scale-[1.01]'
                : selectedFile
                ? 'border-emerald-500/40 bg-slate-900/60'
                : 'border-slate-700/80 hover:border-slate-600 hover:bg-slate-900/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md,.markdown"
              onChange={handleFileChange}
              className="hidden"
            />

            <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400 mb-4 shadow-xl">
              {selectedFile ? <FileCheck className="w-8 h-8" /> : <UploadCloud className="w-8 h-8" />}
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-base font-semibold text-white">{selectedFile.name}</p>
                <p className="text-xs text-slate-400 font-mono">
                  {(selectedFile.size / 1024).toFixed(1)} KB • Click or drop to replace
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-200">
                  Drag & drop your file here, or <span className="text-emerald-400 underline">browse</span>
                </p>
                <p className="text-xs text-slate-500">
                  Supported formats: PDF, DOCX, TXT, MD (Max 25MB)
                </p>
              </div>
            )}
          </div>

          {/* Progress Bar when uploading */}
          {uploading && (
            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
                  {processingStatus === 'UPLOADING' ? 'Uploading file...' : 'Extracting text & indexing vector chunks...'}
                </span>
                <span className="font-mono text-emerald-400">{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="w-full py-3.5 px-4 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-lg shadow-emerald-600/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {uploading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                <span>Process & Ingest Document</span>
              </>
            )}
          </button>
        </div>

        {/* Chunking Settings Card (1 Col) */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-5 h-fit">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Chunking Parameters</h3>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate-300">Chunk Size (Chars)</label>
              <span className="text-xs font-mono text-emerald-400">{chunkSize}</span>
            </div>
            <input
              type="range"
              min="200"
              max="1500"
              step="50"
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Length of each segment sent for embedding. Smaller sizes yield focused citations.
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate-300">Chunk Overlap (Chars)</label>
              <span className="text-xs font-mono text-emerald-400">{chunkOverlap}</span>
            </div>
            <input
              type="range"
              min="0"
              max="200"
              step="10"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Maintains contextual continuity across segment boundaries.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-800/80">
            <p className="text-xs text-slate-400 leading-relaxed">
              Chunking preserves page numbers and original file references so retrieved evidence can be traced back directly.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
