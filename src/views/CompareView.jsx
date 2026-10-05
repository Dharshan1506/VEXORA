import React, { useState } from 'react';
import { GitCompare, ArrowRight, CheckCircle2, AlertCircle, FileText, Sparkles, Layers } from 'lucide-react';

export function CompareView({ documents }) {
  const [docA, setDocA] = useState('Academic Regulations 2025 (v2.0)');
  const [docB, setDocB] = useState('Academic Regulations 2026 (v3.0)');

  const diffSummary = [
    { parameter: 'Minimum Attendance Requirement', oldVal: '75%', newVal: '80%', status: 'changed' },
    { parameter: 'Medical Condonation Limit', oldVal: '15%', newVal: '10%', status: 'changed' },
    { parameter: 'Re-examination Attempt Window', oldVal: '30 Days', newVal: '14 Days', status: 'changed' },
    { parameter: 'Continuous Assessment Weightage', oldVal: '40 Marks', newVal: '50 Marks', status: 'changed' },
    { parameter: 'Sports Condonation Policy', oldVal: 'Not Included', newVal: 'Up to 10% (Verified)', status: 'added' },
  ];

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
            Detect policy parameter shifts, added clauses, and modified regulations across document versions.
          </p>
        </div>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center glass-panel p-4">
        <div className="md:col-span-5">
          <label className="block text-xs font-semibold text-slate-400 mb-1">PREVIOUS VERSION (SOURCE A)</label>
          <select
            value={docA}
            onChange={(e) => setDocA(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            <option>Academic Regulations 2025 (v2.0)</option>
            <option>Examination Handbook 2024 (v1.2)</option>
          </select>
        </div>

        <div className="md:col-span-2 flex justify-center">
          <div className="w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center font-bold">
            VS
          </div>
        </div>

        <div className="md:col-span-5">
          <label className="block text-xs font-semibold text-slate-400 mb-1">REVISED VERSION (SOURCE B)</label>
          <select
            value={docB}
            onChange={(e) => setDocB(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-500"
          >
            <option>Academic Regulations 2026 (v3.0)</option>
            <option>Examination Handbook 2026 (v2.0)</option>
          </select>
        </div>
      </div>

      {/* Parameter Change Matrix Table */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles size={16} className="text-cyan-400" /> Detected Policy Shifts & Amendments
          </h3>
          <span className="text-xs font-mono text-cyan-300 bg-cyan-500/20 px-2.5 py-0.5 rounded-full border border-cyan-500/30">
            5 Key Changes
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/5 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-3">Policy Parameter</th>
                <th className="p-3">2025 Value (v2.0)</th>
                <th className="p-3">2026 Value (v3.0)</th>
                <th className="p-3 text-right">Amendment Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {diffSummary.map((row, idx) => (
                <tr key={idx} className="hover:bg-white/[0.03] transition-colors">
                  <td className="p-3 font-bold text-white">{row.parameter}</td>
                  <td className="p-3 font-mono text-red-400 line-through">{row.oldVal}</td>
                  <td className="p-3 font-mono text-emerald-400 font-bold">{row.newVal}</td>
                  <td className="p-3 text-right">
                    {row.status === 'changed' ? (
                      <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
                        ● Changed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                        + Added Clause
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side-by-Side Clause Diff Preview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Source A Clause */}
        <div className="glass-panel p-6 space-y-3 border-red-500/20">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <span className="text-xs font-bold text-red-400 font-mono">SOURCE A (2025 REGULATIONS)</span>
            <span className="text-[10px] text-slate-500 font-mono">Page 14 • Sec 3.1</span>
          </div>
          <p className="text-xs text-slate-300 bg-red-950/20 p-4 rounded-xl border border-red-500/20 font-mono leading-relaxed">
            "Students must maintain an aggregate attendance of 75% in each semester to qualify for semester examinations. Condonation up to 15% may be granted for medical reasons."
          </p>
        </div>

        {/* Source B Clause */}
        <div className="glass-panel p-6 space-y-3 border-emerald-500/20">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <span className="text-xs font-bold text-emerald-400 font-mono">SOURCE B (2026 REGULATIONS)</span>
            <span className="text-[10px] text-slate-500 font-mono">Page 18 • Sec 4.2</span>
          </div>
          <p className="text-xs text-slate-300 bg-emerald-950/20 p-4 rounded-xl border border-emerald-500/20 font-mono leading-relaxed">
            "Students must maintain a minimum aggregate attendance of 80% across all registered theoretical and laboratory courses. Medical condonation is capped at 10%."
          </p>
        </div>
      </div>
    </div>
  );
}
