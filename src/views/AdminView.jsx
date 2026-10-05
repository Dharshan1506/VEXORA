import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, RefreshCw, Trash2, CheckCircle2, AlertTriangle,
  Cpu, Database, Server, FileText, Activity, Eye
} from 'lucide-react';

export function AdminView({ documents, onDeleteDocument, token }) {
  const [analytics, setAnalytics] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (e) {
      console.error('Analytics fetch failed:', e);
    } finally {
      setLoadingAnalytics(false);
    }
  };

  useEffect(() => { fetchAnalytics(); }, []);

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-white/10 pb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <ShieldAlert size={24} className="text-cyan-400" />
            <span>VEXORA Administration Console</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            System administration for RAG vector index, ingestion pipeline, and retrieval diagnostics.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="px-4 py-2.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-bold text-xs flex items-center gap-2 transition-all"
        >
          <RefreshCw size={14} className={loadingAnalytics ? 'animate-spin' : ''} />
          <span>Refresh Stats</span>
        </button>
      </div>

      {/* Live System Metrics from /api/analytics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
            <span>FastAPI Server</span>
            <Server size={16} className="text-emerald-400" />
          </div>
          <div className="text-xl font-extrabold text-white">Online</div>
          <span className="text-[10px] text-emerald-400 font-mono">Uvicorn :8000 · CORS Active</span>
        </div>

        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
            <span>Vector Embeddings</span>
            <Database size={16} className="text-cyan-400" />
          </div>
          <div className="text-xl font-extrabold text-white">
            {loadingAnalytics ? '...' : (analytics?.total_chunks ?? 0).toLocaleString()}
          </div>
          <span className="text-[10px] text-cyan-300 font-mono">
            Chunks indexed · sentence-transformers
          </span>
        </div>

        <div className="glass-panel p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
            <span>Total Queries</span>
            <Activity size={16} className="text-violet-400" />
          </div>
          <div className="text-xl font-extrabold text-white">
            {loadingAnalytics ? '...' : (analytics?.total_queries ?? 0).toLocaleString()}
          </div>
          <span className="text-[10px] text-violet-300 font-mono">
            RAG pipeline executions
          </span>
        </div>
      </div>

      {/* RAG Pipeline Architecture Info */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Cpu size={16} className="text-cyan-400" /> Active RAG Pipeline
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-[11px]">
          {[
            { label: 'BM25', desc: 'rank-bm25', color: 'text-cyan-300' },
            { label: 'Embeddings', desc: 'all-MiniLM-L6-v2', color: 'text-violet-300' },
            { label: 'RRF Fusion', desc: 'k=60', color: 'text-emerald-300' },
            { label: 'Cross-Encoder', desc: 'ms-marco-MiniLM', color: 'text-amber-300' },
            { label: 'Evidence Guard', desc: 'threshold=0.15', color: 'text-red-300' },
          ].map((s) => (
            <div key={s.label} className="p-3 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
              <div className={`text-xs font-bold ${s.color}`}>{s.label}</div>
              <div className="text-slate-500 font-mono">{s.desc}</div>
              <CheckCircle2 size={12} className="text-emerald-500" />
            </div>
          ))}
        </div>
      </div>

      {/* Indexed Documents Admin Table */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FileText size={16} className="text-cyan-400" /> Indexed Knowledge Files
          <span className="text-[10px] font-mono text-slate-500 ml-2 normal-case">
            ({documents.filter(d => d.status === 'indexed').length} indexed / {documents.length} total)
          </span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/5 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-3">Document</th>
                <th className="p-3">Category</th>
                <th className="p-3">Version</th>
                <th className="p-3">Chunks</th>
                <th className="p-3">OCR</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-slate-500">
                    No documents uploaded yet. Use the Upload button to add university documents.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-white/[0.03]">
                    <td className="p-3">
                      <span className="text-white font-bold font-sans block">{doc.name}</span>
                      <span className="text-[10px] text-slate-500">{doc.id.slice(0, 12)}…</span>
                    </td>
                    <td className="p-3 text-slate-400">{doc.category}</td>
                    <td className="p-3 text-cyan-400 font-mono">{doc.version}</td>
                    <td className="p-3 text-slate-400">{doc.total_chunks ?? '—'}</td>
                    <td className="p-3">
                      {doc.ocr_used
                        ? <span className="text-amber-300">✓ OCR ({(doc.ocr_confidence * 100).toFixed(0)}%)</span>
                        : <span className="text-slate-500">—</span>
                      }
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        doc.status === 'indexed'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : doc.status === 'processing'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-red-500/20 text-red-300'
                      }`}>
                        {doc.status}
                      </span>
                      {doc.superseded_by && (
                        <span className="ml-1 px-1.5 py-0.5 rounded text-[9px] bg-slate-700 text-slate-400">
                          superseded
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => onDeleteDocument(doc.id)}
                        className="px-2 py-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[11px] flex items-center gap-1 ml-auto"
                      >
                        <Trash2 size={10} /> Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
