import React, { useState, useEffect } from 'react';
import { GitCompare, Sparkles, RefreshCw, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';

export function CompareView({ documents = [], token, initialDoc }) {
  const [docAId, setDocAId] = useState(initialDoc?.id || '');
  const [docBId, setDocBId] = useState('');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [selectedChangeIdx, setSelectedChangeIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync initialDoc when passed
  useEffect(() => {
    if (initialDoc?.id && documents.some(d => d.id === initialDoc.id)) {
      setDocAId(initialDoc.id);
      // Select another doc as docBId if available
      const other = documents.find(d => d.id !== initialDoc.id);
      if (other) setDocBId(other.id);
    }
  }, [initialDoc, documents]);

  // Initialize selected documents when documents list loads
  useEffect(() => {
    if (documents.length > 0) {
      if (!docAId || !documents.some(d => d.id === docAId)) {
        setDocAId(documents[0].id);
      }
      if (!docBId || !documents.some(d => d.id === docBId)) {
        setDocBId(documents.length > 1 ? documents[1].id : documents[0].id);
      }
    }
  }, [documents]);

  const handleCompare = async (sourceId = docAId, targetId = docBId) => {
    if (!sourceId || !targetId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/documents/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          source_document_id: sourceId,
          target_document_id: targetId,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Comparison failed (HTTP ${res.status})`);
      }

      const data = await res.json();
      setComparisonResult(data);
      setSelectedChangeIdx(0);
    } catch (err) {
      setError(err.message);
      setComparisonResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Trigger compare whenever doc selections change
  useEffect(() => {
    if (docAId && docBId) {
      handleCompare(docAId, docBId);
    }
  }, [docAId, docBId]);

  const docA = documents.find(d => d.id === docAId);
  const docB = documents.find(d => d.id === docBId);
  const changes = comparisonResult?.changes || [];
  const activeChange = changes[selectedChangeIdx] || changes[0] || null;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-white/10 pb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <GitCompare size={24} className="text-cyan-400" />
            <span>Policy & Version Comparison</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Compare real uploaded policy documents, extract parameter shifts, added clauses, and regulation updates.
          </p>
        </div>
        <button
          onClick={() => handleCompare(docAId, docBId)}
          disabled={loading || !docAId || !docBId}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 disabled:opacity-50 text-white font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-1.5 shadow-lg shadow-cyan-500/20"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>{loading ? 'Comparing...' : 'Re-run Compare'}</span>
        </button>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center glass-panel p-4">
        <div className="md:col-span-5">
          <label className="block text-xs font-semibold text-slate-400 mb-1">
            PREVIOUS VERSION (SOURCE A)
          </label>
          <select
            value={docAId}
            onChange={(e) => setDocAId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            {documents.length === 0 ? (
              <option value="">No uploaded documents found</option>
            ) : (
              documents.map((d) => (
                <option key={`a-${d.id}`} value={d.id}>
                  {d.name} ({d.version || 'v1.0'}) — {d.category}
                </option>
              ))
            )}
          </select>
        </div>

        <div className="md:col-span-2 flex justify-center">
          <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center font-bold text-xs shadow-lg">
            VS
          </div>
        </div>

        <div className="md:col-span-5">
          <label className="block text-xs font-semibold text-slate-400 mb-1">
            REVISED VERSION (SOURCE B)
          </label>
          <select
            value={docBId}
            onChange={(e) => setDocBId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            {documents.length === 0 ? (
              <option value="">No uploaded documents found</option>
            ) : (
              documents.map((d) => (
                <option key={`b-${d.id}`} value={d.id}>
                  {d.name} ({d.version || 'v1.0'}) — {d.category}
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading indicator */}
      {loading && !error && (
        <div className="p-8 text-center glass-panel space-y-2">
          <RefreshCw size={24} className="animate-spin text-cyan-400 mx-auto" />
          <p className="text-sm text-slate-300 font-semibold">Comparing Document Contents...</p>
          <p className="text-xs text-slate-500 font-mono">
            Extracting clauses, comparing numerical parameters, and identifying changes
          </p>
        </div>
      )}

      {/* Results */}
      {!loading && comparisonResult && (
        <>
          {/* Parameter Change Matrix Table */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles size={16} className="text-cyan-400" />
                Detected Policy Shifts & Amendments
              </h3>
              <span className="text-xs font-mono text-cyan-300 bg-cyan-500/20 px-2.5 py-0.5 rounded-full border border-cyan-500/30">
                {changes.length} {changes.length === 1 ? 'Change' : 'Changes'} Detected
              </span>
            </div>

            {changes.length === 0 ? (
              <div className="text-center py-8 space-y-2 text-slate-400">
                <CheckCircle2 size={28} className="mx-auto text-emerald-400" />
                <p className="text-xs font-medium text-slate-200">
                  {comparisonResult.message || 'No policy parameter differences detected between these document versions.'}
                </p>
                {docAId === docBId && (
                  <p className="text-[11px] text-slate-500">
                    Select two different documents in the dropdowns above to compare shifts.
                  </p>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-white/5 text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="p-3">Policy Parameter</th>
                      <th className="p-3">{docA?.name || 'Source A'} ({docA?.version || 'v1.0'})</th>
                      <th className="p-3">{docB?.name || 'Source B'} ({docB?.version || 'v2.0'})</th>
                      <th className="p-3 text-right">Amendment Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {changes.map((row, idx) => {
                      const isSelected = selectedChangeIdx === idx;
                      return (
                        <tr
                          key={idx}
                          onClick={() => setSelectedChangeIdx(idx)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-cyan-500/15 border-l-2 border-cyan-400' : 'hover:bg-white/[0.03]'
                          }`}
                        >
                          <td className="p-3 font-bold text-white flex items-center gap-2">
                            <span>{row.parameter}</span>
                            {isSelected && (
                              <span className="text-[10px] text-cyan-400 font-mono">(active preview)</span>
                            )}
                          </td>
                          <td className="p-3 font-mono text-red-400 line-through">
                            {row.old_value}
                          </td>
                          <td className="p-3 font-mono text-emerald-400 font-bold">
                            {row.new_value}
                          </td>
                          <td className="p-3 text-right">
                            {row.type === 'changed' && (
                              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
                                ● Changed
                              </span>
                            )}
                            {row.type === 'added' && (
                              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                                + Added Clause
                              </span>
                            )}
                            {row.type === 'removed' && (
                              <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 text-[10px] font-bold">
                                − Removed Clause
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Side-by-Side Real Clause Diff Preview */}
          {activeChange && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span className="font-semibold uppercase tracking-wider text-slate-300">
                  Active Comparison Clause: <span className="text-cyan-300 font-bold">{activeChange.parameter}</span>
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  Click any row in the table above to preview corresponding clauses
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Source A Clause */}
                <div className="glass-panel p-6 space-y-3 border-red-500/20">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10">
                    <span className="text-xs font-bold text-red-400 font-mono truncate max-w-[240px]">
                      SOURCE A: {activeChange.source_a?.doc_name || docA?.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {activeChange.source_a?.page != null ? `Page ${activeChange.source_a.page}` : 'Page N/A'}
                      {activeChange.source_a?.section ? ` • Sec ${activeChange.source_a.section}` : ''}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 bg-red-950/20 p-4 rounded-xl border border-red-500/20 font-mono leading-relaxed">
                    "{activeChange.source_a?.snippet || 'No clause text found.'}"
                  </p>
                </div>

                {/* Source B Clause */}
                <div className="glass-panel p-6 space-y-3 border-emerald-500/20">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10">
                    <span className="text-xs font-bold text-emerald-400 font-mono truncate max-w-[240px]">
                      SOURCE B: {activeChange.source_b?.doc_name || docB?.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {activeChange.source_b?.page != null ? `Page ${activeChange.source_b.page}` : 'Page N/A'}
                      {activeChange.source_b?.section ? ` • Sec ${activeChange.source_b.section}` : ''}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 bg-emerald-950/20 p-4 rounded-xl border border-emerald-500/20 font-mono leading-relaxed">
                    "{activeChange.source_b?.snippet || 'No clause text found.'}"
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
