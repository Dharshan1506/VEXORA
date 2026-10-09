import React, { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  Layers,
  Sparkles,
  Calendar,
  ExternalLink,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

export function DocumentViewer({ document, onAskAboutDoc, token }) {
  const [activeDocId, setActiveDocId] = useState(document?.id || '');
  const [docContent, setDocContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('text'); // 'text' | 'pdf'
  const [selectedSection, setSelectedSection] = useState(null);

  useEffect(() => {
    if (document?.id) {
      setActiveDocId(document.id);
    }
  }, [document?.id]);

  useEffect(() => {
    if (!activeDocId) {
      setDocContent(null);
      return;
    }

    const fetchContent = async () => {
      setLoading(true);
      setError(null);
      try {
        const authToken = token || localStorage.getItem('vexora_token');
        const res = await fetch(`/api/documents/${activeDocId}/content`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        });
        if (!res.ok) {
          throw new Error(`Failed to load document content (HTTP ${res.status})`);
        }
        const data = await res.json();
        setDocContent(data);
        if (data.sections?.length > 0) {
          setSelectedSection(data.sections[0]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [activeDocId, token]);

  if (!document && !activeDocId) {
    return (
      <div className="h-[calc(100vh-4rem)] flex items-center justify-center p-6 text-center">
        <div className="glass-panel p-8 max-w-md space-y-3">
          <FileText size={36} className="mx-auto text-slate-500" />
          <h2 className="text-base font-bold text-white">No Document Selected</h2>
          <p className="text-xs text-slate-400">
            Open the Knowledge Vault and click "View Document" on any uploaded policy to inspect its full text and extracted sections.
          </p>
        </div>
      </div>
    );
  }

  const sections = docContent?.sections || [];
  const fullText = docContent?.full_text || '';
  const detectedEntities = docContent?.detected_entities || [];

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">
      {/* LEFT COLUMN: Outline & Section Navigator */}
      <div className="w-64 bg-[#070b19]/90 border-r border-white/10 flex flex-col justify-between shrink-0">
        <div className="p-4 space-y-2 border-b border-white/10">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Document Structure</span>
          <h2 className="text-xs font-bold text-white leading-snug line-clamp-2">
            {docContent?.name || document?.name || 'Document'}
          </h2>
          <span className="text-[10px] font-mono text-cyan-300">
            {docContent?.version || document?.version || 'v1.0'} • {docContent?.category || document?.category || 'General'}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {sections.length === 0 ? (
            <p className="text-[11px] text-slate-500 p-2 italic">
              {loading ? 'Loading sections...' : 'No structured section headers detected.'}
            </p>
          ) : (
            sections.map((sec) => (
              <button
                key={sec.id}
                onClick={() => setSelectedSection(sec)}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition-colors ${
                  selectedSection?.id === sec.id
                    ? 'bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/30'
                    : 'text-slate-300 hover:bg-white/5 hover:text-cyan-300'
                }`}
              >
                <span className="truncate max-w-[140px]">{sec.title}</span>
                <span className="text-[10px] text-slate-500 font-mono">p.{sec.page}</span>
              </button>
            ))
          )}
        </div>

        {/* View mode toggle if PDF exists */}
        {docContent?.has_pdf_file && (
          <div className="p-3 border-t border-white/10">
            <div className="flex rounded-lg bg-slate-900 p-1 border border-white/5">
              <button
                onClick={() => setViewMode('text')}
                className={`flex-1 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                  viewMode === 'text' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'
                }`}
              >
                Extracted Text
              </button>
              <button
                onClick={() => setViewMode('pdf')}
                className={`flex-1 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                  viewMode === 'pdf' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'
                }`}
              >
                Original PDF
              </button>
            </div>
          </div>
        )}
      </div>

      {/* CENTER COLUMN: Document Reader */}
      <div className="flex-1 flex flex-col justify-between bg-[#070b19]/40 relative overflow-hidden">
        {/* Header & Search */}
        <div className="p-4 bg-[#070b19]/80 border-b border-white/10 backdrop-blur-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={18} className="text-cyan-400" />
            <span className="text-sm font-bold text-white truncate max-w-sm">
              {docContent?.name || document?.name}
            </span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[10px] font-bold">
              {docContent?.version || document?.version || 'v1.0'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative w-64">
              <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search in document..."
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {onAskAboutDoc && (
              <button
                onClick={() => onAskAboutDoc(docContent?.name || document?.name)}
                className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
              >
                <Sparkles size={13} />
                <span>Ask VEXORA</span>
              </button>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 max-w-5xl mx-auto w-full">
          {loading ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <RefreshCw size={24} className="animate-spin text-cyan-400 mx-auto" />
              <p className="text-xs">Loading document text from vault...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          ) : viewMode === 'pdf' && docContent?.has_pdf_file ? (
            <div className="h-full w-full rounded-2xl overflow-hidden border border-white/10 bg-slate-950">
              <iframe
                src={`/api/documents/${activeDocId}/file`}
                title={docContent?.name}
                className="w-full h-[calc(100vh-10rem)] border-0"
              />
            </div>
          ) : (
            <div className="glass-panel p-6 space-y-4 border-cyan-500/20 shadow-2xl">
              {selectedSection && (
                <div className="pb-3 border-b border-white/10 flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-400">
                    {selectedSection.title.toUpperCase()} • PAGE {selectedSection.page}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {docContent?.chunks?.length || 0} Chunks Indexed
                  </span>
                </div>
              )}

              <div className="text-sm text-slate-200 font-sans leading-relaxed whitespace-pre-wrap">
                {searchTerm ? (
                  fullText
                    .split('\n')
                    .filter((line) => line.toLowerCase().includes(searchTerm.toLowerCase()))
                    .map((matchLine, idx) => (
                      <p key={idx} className="p-2 rounded bg-cyan-500/10 border border-cyan-500/20 my-1 font-mono text-xs text-cyan-100">
                        {matchLine}
                      </p>
                    ))
                ) : (
                  fullText || 'No readable text content extracted.'
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* RIGHT COLUMN: Extracted Metadata & Entities */}
      <div className="w-80 bg-[#070b19]/90 border-l border-white/10 flex flex-col justify-between shrink-0 overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Extracted Metadata</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          <div className="glass-panel p-4 space-y-3">
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Category</span>
              <span className="font-bold text-white">{docContent?.category || document?.category || 'General'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Version Tag</span>
              <span className="font-mono text-cyan-300 font-bold">{docContent?.version || document?.version || 'v1.0'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Upload Date</span>
              <span className="font-mono text-slate-300">{docContent?.upload_date || document?.upload_date || 'Recent'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Indexed Chunks</span>
              <span className="font-mono text-slate-200">
                {docContent?.total_chunks || document?.total_chunks || docContent?.chunks?.length || 0} Chunks
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Indexing Status</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold inline-block mt-0.5">
                ● {docContent?.status || document?.status || 'indexed'}
              </span>
            </div>
          </div>

          <div className="glass-panel p-4 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Detected Policy Entities
            </span>
            {detectedEntities.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic">No specific percentages or numerical clauses identified.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {detectedEntities.map((ent, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[10px] font-mono"
                  >
                    {ent}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
