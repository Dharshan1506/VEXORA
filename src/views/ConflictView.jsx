import React, { useState, useEffect } from 'react';
import {
  AlertTriangle, ShieldCheck, RefreshCw, FileText, CheckCircle2
} from 'lucide-react';

export function ConflictView({ token }) {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchConflicts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/documents/conflicts', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setConflicts(data.conflicts || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchConflicts();
  }, [token]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-in fade-in duration-300">
      {/* Warning Banner */}
      <div className="p-6 rounded-3xl bg-amber-500/10 border border-amber-500/30 backdrop-blur-xl flex items-start gap-4 shadow-xl">
        <div className="p-3 rounded-2xl bg-amber-500/20 text-amber-400 shrink-0">
          <AlertTriangle size={28} />
        </div>
        <div className="space-y-1 flex-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white">DOCUMENT CONFLICT DETECTOR</h1>
              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                {conflicts.length} Conflict{conflicts.length !== 1 ? 's' : ''} Found
              </span>
            </div>
            <button
              onClick={fetchConflicts}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          <p className="text-slate-300 text-xs leading-relaxed">
            VEXORA's cross-document verification engine detects conflicting values across
            uploaded university policy documents. Conflicts are detected automatically on upload.
          </p>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
          Failed to load conflicts: {error}
        </div>
      )}

      {/* Loading */}
      {loading && !error && (
        <div className="text-center py-12 text-slate-400 text-sm">
          <RefreshCw size={20} className="animate-spin mx-auto mb-3 text-cyan-400" />
          Scanning documents for conflicts...
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && conflicts.length === 0 && (
        <div className="text-center py-16 space-y-3">
          <CheckCircle2 size={32} className="mx-auto text-emerald-400" />
          <p className="text-white font-bold">No conflicts detected</p>
          <p className="text-slate-400 text-xs max-w-sm mx-auto">
            No conflicting percentage values or policy statements found across
            your uploaded documents. Upload additional documents to trigger analysis.
          </p>
        </div>
      )}

      {/* Conflict Cards */}
      <div className="space-y-6">
        {conflicts.map((item, idx) => (
          <div key={item.id || idx} className="glass-panel p-6 space-y-5 border-amber-500/20">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400" />
                {item.conflict_type === 'percentage_mismatch'
                  ? 'Percentage Value Conflict'
                  : item.conflict_type || 'Content Conflict'}
              </h3>
              <span className="text-xs font-mono text-amber-300 bg-amber-500/20 px-2.5 py-0.5 rounded-full border border-amber-500/30">
                ⚠ Conflict Flagged
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Document A */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-slate-400" />
                  <span className="text-xs font-bold text-slate-300">
                    {item.doc_name_a || `Document ID: ${item.document_id_a}`}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono bg-slate-950/60 p-3 rounded-xl border border-white/5">
                  {item.description || 'No description available.'}
                </p>
                <span className="inline-block text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  Older / Potentially Superseded
                </span>
              </div>

              {/* Document B */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-cyan-500/30 space-y-3">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-cyan-400" />
                  <span className="text-xs font-bold text-cyan-300">
                    {item.doc_name_b || `Document ID: ${item.document_id_b}`}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-mono bg-slate-950/60 p-3 rounded-xl border border-white/5">
                  Detected at: {new Date(item.detected_at).toLocaleString()}
                </p>
                <span className="inline-block text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  ✓ Newer Upload
                </span>
              </div>
            </div>

            {/* Resolution Note */}
            <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center gap-3 text-xs">
              <ShieldCheck size={20} className="text-cyan-400 shrink-0" />
              <div>
                <span className="font-bold text-cyan-300 block">VEXORA Recommendation:</span>
                <p className="text-slate-300 mt-0.5">
                  Review both documents and confirm which version is authoritative.
                  The newer upload is preferred in retrieval unless it is explicitly marked as superseded.
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
