import React, { useState } from 'react';
import {
  Upload,
  Search,
  Filter,
  Grid,
  List,
  FileText,
  Trash2,
  Eye,
  GitCompare,
  Download,
  Layers,
  CheckCircle2,
  Clock,
  Sparkles,
  Tag
} from 'lucide-react';

export function VaultView({ documents, onUploadClick, onViewDocument, onCompareDocument, onDeleteDocument }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [viewMode, setViewMode] = useState('grid');

  const categories = ['All', 'Academic', 'Examination', 'Hostel', 'Placement', 'Rules', 'General'];

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) || doc.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = selectedCategory === 'All' || doc.category.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCat;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <span>Knowledge Vault</span>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              {filteredDocs.length} Documents
            </span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Centralized index of all official university regulations, handbooks, and policy files.
          </p>
        </div>

        <button
          onClick={onUploadClick}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 via-violet-600 to-magenta-500 hover:from-cyan-400 hover:to-magenta-400 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
        >
          <Upload size={16} /> Upload New Document
        </button>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200 border border-transparent'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search & View Toggle */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search vault files..."
              className="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-900/80 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-white/10">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-white/10 text-cyan-400' : 'text-slate-500'}`}
              title="Grid View"
            >
              <Grid size={16} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-white/10 text-cyan-400' : 'text-slate-500'}`}
              title="List View"
            >
              <List size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Grid or List View */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocs.map((doc) => (
            <div key={doc.id} className="glass-panel-interactive p-6 space-y-4 flex flex-col justify-between group">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                    <FileText size={24} />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono font-bold text-cyan-300">
                      {doc.version || 'v1.0'}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                      ● Indexed
                    </span>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-1">
                    {doc.name}
                  </h3>
                  <span className="text-[11px] text-slate-400 font-medium block mt-0.5">{doc.category}</span>
                </div>
              </div>

              {/* Stats Footer */}
              <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span className="flex items-center gap-1">
                  <Layers size={14} className="text-cyan-400" /> {doc.chunks || 450} Chunks
                </span>
                <span>{doc.uploadDate || '2026-09-20'}</span>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => onViewDocument(doc)}
                  className="flex-1 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 font-semibold text-xs transition-colors flex items-center justify-center gap-1"
                >
                  <Eye size={14} /> View Document
                </button>
                <button
                  onClick={() => onCompareDocument(doc)}
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-400 hover:text-white"
                  title="Compare Versions"
                >
                  <GitCompare size={14} />
                </button>
                <button
                  onClick={() => onDeleteDocument(doc.id)}
                  className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300"
                  title="Delete Document"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* List View Table */
        <div className="glass-panel overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-white/5 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="p-4">Document Name</th>
                <th className="p-4">Category</th>
                <th className="p-4">Version</th>
                <th className="p-4">Chunks</th>
                <th className="p-4">Uploaded</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-white/[0.03] transition-colors">
                  <td className="p-4 font-bold text-white flex items-center gap-2">
                    <FileText size={18} className="text-cyan-400" />
                    {doc.name}
                  </td>
                  <td className="p-4">{doc.category}</td>
                  <td className="p-4 font-mono font-bold text-cyan-300">{doc.version || 'v1.0'}</td>
                  <td className="p-4 font-mono text-slate-400">{doc.chunks || 450}</td>
                  <td className="p-4 text-slate-400">{doc.uploadDate || '2026-09-20'}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                      ● Indexed
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-2">
                    <button
                      onClick={() => onViewDocument(doc)}
                      className="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-semibold"
                    >
                      View
                    </button>
                    <button
                      onClick={() => onDeleteDocument(doc.id)}
                      className="px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
