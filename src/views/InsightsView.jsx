import React from 'react';
import { BarChart3, TrendingUp, Layers, BookOpen, Search, Sparkles } from 'lucide-react';

export function InsightsView() {
  const categoryStats = [
    { name: 'Academic Regulations', count: 42, percentage: 35, color: 'bg-cyan-500' },
    { name: 'Examination Guidelines', count: 28, percentage: 23, color: 'bg-violet-500' },
    { name: 'Campus Placement Rules', count: 22, percentage: 18, color: 'bg-magenta-500' },
    { name: 'Hostel & Housing Rules', count: 18, percentage: 15, color: 'bg-emerald-500' },
    { name: 'Scholarships & Grants', count: 10, percentage: 9, color: 'bg-amber-500' },
  ];

  const topQueries = [
    { query: 'Minimum attendance percentage required for end semester exams', count: 1420 },
    { query: 'Placement eligibility CGPA cutoff criteria', count: 980 },
    { query: 'Internal examination mark weightage and re-test rules', count: 740 },
    { query: 'Hostel late entry curfew timings and leave permission', count: 620 },
    { query: 'Scholarship fee waiver application procedure', count: 410 },
  ];

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto animate-in fade-in duration-300">
      <div className="border-b border-white/10 pb-6">
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <BarChart3 size={24} className="text-cyan-400" />
          <span>University Knowledge Analytics & Insights</span>
        </h1>
        <p className="text-slate-400 text-xs mt-1">
          Real-time intelligence analytics tracking knowledge coverage, query volume, and document retrieval efficiency.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total User Queries Processed', val: '14,820', change: '+18% this week', color: 'text-cyan-400' },
          { label: 'Mean Retrieval Latency', val: '140 ms', change: 'Hybrid BM25 + Vector', color: 'text-emerald-400' },
          { label: 'Citations Verified', val: '99.4%', change: 'Zero hallucinated claims', color: 'text-violet-400' },
          { label: 'Knowledge Base Chunks', val: '3,842', change: '14 Verified Documents', color: 'text-magenta-400' },
        ].map((s, i) => (
          <div key={i} className="glass-panel p-5 space-y-2">
            <span className="text-xs font-semibold text-slate-400">{s.label}</span>
            <div className={`text-2xl font-extrabold ${s.color}`}>{s.val}</div>
            <span className="text-[11px] text-slate-400 font-medium">{s.change}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Document Categories Distribution Bar Progress */}
        <div className="lg:col-span-6 glass-panel p-6 space-y-6">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Layers size={16} className="text-cyan-400" /> Knowledge Chunks Distribution by Category
          </h3>
          <div className="space-y-4">
            {categoryStats.map((c, i) => (
              <div key={i} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-white">{c.name}</span>
                  <span className="font-mono text-cyan-300 font-bold">{c.count} docs ({c.percentage}%)</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden">
                  <div className={`h-full ${c.color} rounded-full transition-all duration-500`} style={{ width: `${c.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Most Asked University Topics Table */}
        <div className="lg:col-span-6 glass-panel p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Search size={16} className="text-cyan-400" /> Most Frequently Asked Student Queries
          </h3>
          <div className="space-y-3">
            {topQueries.map((q, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 max-w-[280px]">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center font-mono font-bold text-[10px] shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-slate-200 font-medium truncate">{q.query}</span>
                </div>
                <span className="font-mono font-bold text-cyan-300 shrink-0">{q.count} searches</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
