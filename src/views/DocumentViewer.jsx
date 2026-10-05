import React, { useState } from 'react';
import {
  FileText,
  Search,
  BookOpen,
  Calendar,
  Layers,
  Sparkles,
  Tag,
  Copy,
  ExternalLink,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export function DocumentViewer({ document, onAskAboutDoc }) {
  const [activeTab, setActiveTab] = useState('text');
  const [searchTerm, setSearchTerm] = useState('');

  const docData = document || {
    name: 'Academic Regulations 2026',
    category: 'Academic',
    version: 'v3.0',
    publishedDate: '2026-09-01',
    effectiveDate: '2026-11-01',
    chunks: 842,
    sections: [
      { id: 'sec1', title: '1.0 Short Title & Commencement', page: 1 },
      { id: 'sec2', title: '2.0 Academic Credit System', page: 5 },
      { id: 'sec3', title: '3.0 Evaluation & Grading Scheme', page: 12 },
      { id: 'sec4', title: '4.0 Attendance Regulations', page: 18 },
      { id: 'sec5', title: '5.0 Examination & Condonation Rules', page: 24 },
    ],
    content: `SECTION 4.2: ATTENDANCE & CONDONATION REGULATIONS

1. Attendance Requirement:
Students enrolled in undergraduate and postgraduate programs must maintain a minimum aggregate attendance of 80% across all registered theoretical and laboratory courses in a semester to be eligible to appear for the Semester End Examinations (SEE).

2. Medical & Sports Condonation:
In cases of severe medical prolonged illness (hospitalization) or officially sanctioned representation of the University in national level sports or academic symposiums, condonation of up to 10% attendance may be granted by the Academic Council upon submission of verified documentation.

3. Detention Penalty:
Students with attendance falling below 70% under any circumstances shall be detained from the semester examination and must re-register for the entire course unit in the subsequent academic session.`
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">
      {/* LEFT COLUMN: Outline & Section Navigator */}
      <div className="w-64 bg-[#070b19]/90 border-r border-white/10 flex flex-col justify-between shrink-0">
        <div className="p-4 space-y-3 border-b border-white/10">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Document Structure</span>
          <h2 className="text-xs font-bold text-white leading-snug line-clamp-2">{docData.name}</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {docData.sections.map((sec) => (
            <button
              key={sec.id}
              className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-300 hover:bg-white/5 hover:text-cyan-300 flex items-center justify-between transition-colors"
            >
              <span className="truncate">{sec.title}</span>
              <span className="text-[10px] text-slate-500 font-mono">p.{sec.page}</span>
            </button>
          ))}
        </div>
      </div>

      {/* CENTER COLUMN: Document Text Reader */}
      <div className="flex-1 flex flex-col justify-between bg-[#070b19]/40 relative overflow-hidden">
        {/* Document Header & Search Toolbar */}
        <div className="p-4 bg-[#070b19]/80 border-b border-white/10 backdrop-blur-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={18} className="text-cyan-400" />
            <span className="text-sm font-bold text-white">{docData.name}</span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[10px] font-bold">
              {docData.version}
            </span>
          </div>

          <div className="relative w-64">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search in document text..."
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-4xl mx-auto w-full">
          <div className="glass-panel p-8 space-y-4 border-cyan-500/20 shadow-2xl">
            <div className="pb-4 border-b border-white/10 flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-cyan-400">PAGE 18 • SECTION 4.2</span>
              <button
                onClick={() => onAskAboutDoc && onAskAboutDoc(docData.name)}
                className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-bold text-xs flex items-center gap-1.5 shadow-md"
              >
                <Sparkles size={14} /> Ask VEXORA About This Document
              </button>
            </div>

            <pre className="text-sm text-slate-200 font-sans leading-relaxed whitespace-pre-wrap">
              {docData.content}
            </pre>
          </div>
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
              <span className="font-bold text-white">{docData.category}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Effective Date</span>
              <span className="font-mono text-cyan-300">{docData.effectiveDate || '2026-11-01'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Indexed Chunks</span>
              <span className="font-mono text-slate-200">{docData.chunks} Chunks</span>
            </div>
          </div>

          <div className="glass-panel p-4 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Detected Entities</span>
            <div className="flex flex-wrap gap-1.5">
              <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[10px]">
                80% Attendance
              </span>
              <span className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20 text-[10px]">
                10% Condonation
              </span>
              <span className="px-2 py-0.5 rounded bg-magenta-500/10 text-magenta-300 border border-magenta-500/20 text-[10px]">
                70% Detention
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
