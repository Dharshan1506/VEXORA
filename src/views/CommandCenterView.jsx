
import React, { useState } from 'react';
import {
  Search,
  Mic,
  Upload,
  Sparkles,
  BookOpen,
  FileCheck,
  GitCompare,
  ArrowUpRight,
  Database,
  Layers,
  Clock,
  TrendingUp,
  ShieldCheck,
  FileText
} from 'lucide-react';

export function CommandCenterView({ user, documents = [], onNavigate, onUploadClick, onSearchQuery }) {
  const [query, setQuery] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearchQuery(query);
  };

  const quickActions = [
    { label: 'Ask a Question', icon: Sparkles, color: 'from-cyan-500/20 to-blue-600/20 border-cyan-500/30 text-cyan-300', view: 'chat' },
    { label: 'Search Documents', icon: BookOpen, color: 'from-violet-500/20 to-purple-600/20 border-violet-500/30 text-violet-300', view: 'vault' },
    { label: 'Upload Document', icon: Upload, color: 'from-magenta-500/20 to-pink-600/20 border-magenta-500/30 text-magenta-300', action: onUploadClick },
    { label: 'Compare Policies', icon: GitCompare, color: 'from-emerald-500/20 to-teal-600/20 border-emerald-500/30 text-emerald-300', view: 'compare' },
  ];

  const totalDocs = documents.length;
  const totalChunks = documents.reduce((acc, d) => acc + (d.total_chunks || 0), 0);
  const categoriesCount = new Set(documents.map(d => d.category || 'General')).size;
  const latestVersion = documents[0]?.version || 'v1.0';

  const stats = [
    { label: 'Knowledge Categories', value: String(categoriesCount || 1), change: 'Categorized', icon: Database, color: 'text-cyan-400' },
    { label: 'Indexed Documents', value: String(totalDocs), change: '100% verified', icon: FileText, color: 'text-violet-400' },
    { label: 'Indexed Knowledge Chunks', value: totalChunks.toLocaleString(), change: 'Vector & BM25', icon: Layers, color: 'text-magenta-400' },
    { label: 'Latest Indexed Version', value: latestVersion, change: 'Active in RAG', icon: Clock, color: 'text-emerald-400' },
  ];

  const recentDocuments = documents.slice(0, 5).map(d => ({
    title: d.name,
    category: d.category || 'General',
    version: d.version || 'v1.0',
    chunks: d.total_chunks || 0,
    date: d.upload_date || (d.created_at ? d.created_at.slice(0, 10) : 'Recent'),
    status: d.status || 'indexed',
  }));

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="relative p-8 rounded-3xl bg-gradient-to-r from-slate-900/80 via-[#0d142a]/90 to-violet-950/40 border border-white/10 backdrop-blur-2xl overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-xs font-semibold text-cyan-300">
            <Sparkles size={14} className="text-cyan-400 animate-pulse" />
            <span>VEXORA Knowledge Intelligence Active</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Good morning, <span className="text-gradient-cyan">{user?.name || 'Scholar'}</span>
          </h1>
          <p className="text-slate-300 text-sm sm:text-base max-w-2xl">
            What would you like to discover today across your university's policies, regulations, and academic records?
          </p>
        </div>

        {/* Large Hero AI Search Box */}
        <form onSubmit={handleSearchSubmit} className="relative mt-8 z-10">
          <div className="relative flex items-center rounded-2xl bg-[#070b19]/90 border border-cyan-500/40 shadow-2xl shadow-cyan-500/10 backdrop-blur-2xl overflow-hidden group focus-within:border-cyan-400 focus-within:shadow-cyan-500/20 transition-all">
            <div className="pl-5 text-cyan-400">
              <Search size={22} />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask VEXORA anything about attendance, exams, hostels, placement rules..."
              className="w-full py-4 pl-4 pr-32 bg-transparent text-white placeholder-slate-400 text-base focus:outline-none"
            />
            <div className="absolute right-3 flex items-center gap-2">
              <button
                type="button"
                onClick={onUploadClick}
                className="p-2 rounded-xl text-slate-400 hover:text-cyan-300 hover:bg-white/10 transition-colors"
                title="Attach Document"
              >
                <Upload size={18} />
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-1.5"
              >
                <span>Discover</span>
                <ArrowUpRight size={16} />
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">Quick Intelligence Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, i) => {
            const Icon = action.icon;
            return (
              <button
                key={i}
                onClick={() => {
                  if (action.action) action.action();
                  else if (action.view) onNavigate(action.view);
                }}
                className={`p-5 rounded-2xl bg-gradient-to-br ${action.color} border backdrop-blur-xl hover:scale-[1.02] transition-all duration-200 text-left flex items-center justify-between group shadow-lg`}
              >
                <div className="space-y-2">
                  <Icon size={24} />
                  <span className="block font-bold text-slate-100 text-sm group-hover:text-white">{action.label}</span>
                </div>
                <ArrowUpRight size={18} className="text-slate-400 group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Stats Cards & Mini Network Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 4 Stat Cards */}
        <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">{s.label}</span>
                  <div className={`p-2 rounded-xl bg-white/5 ${s.color}`}>
                    <Icon size={18} />
                  </div>
                </div>
                <div className="mt-4">
                  <div className="text-2xl font-extrabold text-white">{s.value}</div>
                  <span className="text-[11px] text-emerald-400 font-medium">{s.change}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Mini Knowledge Network Card */}
        <div className="lg:col-span-4 glass-panel p-5 flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Live Knowledge Graph</h3>
            <button
              onClick={() => onNavigate('network')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
            >
              Expand <ArrowUpRight size={12} />
            </button>
          </div>

          {/* Interactive Mini Node Canvas preview */}
          <div className="relative h-40 rounded-xl bg-slate-950/60 border border-white/5 flex items-center justify-center p-4">
            <div className="absolute inset-0 flex items-center justify-center opacity-30">
              <div className="w-24 h-24 rounded-full border border-cyan-500/40 animate-ping" />
              <div className="w-40 h-40 rounded-full border border-violet-500/20" />
            </div>
            <div className="relative z-10 text-center space-y-2">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                <Database size={20} />
              </div>
              <p className="text-xs font-medium text-slate-200">14 Verified Documents Connected</p>
              <span className="text-[10px] text-slate-400">842 Chunks • 12 Topics</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Document Ingestions Table */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recent Knowledge Ingestions</h3>
            <p className="text-xs text-slate-400">Latest official university regulations and policies indexed</p>
          </div>
          <button
            onClick={() => onNavigate('vault')}
            className="text-xs font-bold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            View All Vault Documents &rarr;
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/5 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-3 rounded-l-xl">Document Name</th>
                <th className="p-3">Category</th>
                <th className="p-3">Version</th>
                <th className="p-3">Chunks</th>
                <th className="p-3">Uploaded</th>
                <th className="p-3 rounded-r-xl text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {recentDocuments.map((doc, idx) => (
                <tr key={idx} className="hover:bg-white/[0.03] transition-colors">
                  <td className="p-3 font-semibold text-white flex items-center gap-2">
                    <FileText size={16} className="text-cyan-400" />
                    {doc.title}
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[11px]">
                      {doc.category}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-cyan-300 font-bold">{doc.version}</td>
                  <td className="p-3 font-mono text-slate-400">{doc.chunks}</td>
                  <td className="p-3 text-slate-400">{doc.date}</td>
                  <td className="p-3 text-right">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                      ● Indexed
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
