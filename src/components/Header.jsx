import React, { useState } from 'react';
import {
  Search,
  Bell,
  Sun,
  Moon,
  Sparkles,
  ShieldCheck,
  Zap,
  Globe,
  X
} from 'lucide-react';

export function Header({ currentView, theme, setTheme, onOpenGlobalSearch, isBackendLive }) {
  const [showNotifications, setShowNotifications] = useState(false);

  const titles = {
    command: 'Command Center',
    chat: 'Ask VEXORA — Multimodal RAG Assistant',
    vault: 'Knowledge Vault & Repository',
    viewer: 'Advanced Document Viewer',
    compare: 'Policy & Version Comparison Engine',
    conflict: 'Conflict Detector & Verification',
    network: 'Interactive Knowledge Graph',
    insights: 'University Analytics & Insights',
    admin: 'System Administration & Ingestion',
    settings: 'Platform Settings & Configuration'
  };

  const notifications = [
    { id: 1, title: 'Academic Regulations 2026 Indexed', time: '10m ago', type: 'info' },
    { id: 2, title: 'Conflict detected: Attendance Policy', time: '1h ago', type: 'warning' },
    { id: 3, title: 'Vector index synced (842 chunks)', time: '3h ago', type: 'success' },
  ];

  return (
    <header className="relative z-10 h-16 bg-[#070b19]/60 backdrop-blur-xl border-b border-white/10 px-6 flex items-center justify-between">
      {/* View Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-white tracking-wide">
          {titles[currentView] || 'VEXORA Platform'}
        </h1>
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[11px] font-semibold text-cyan-300">
          <Zap size={12} className="text-cyan-400 animate-pulse" />
          <span>Multimodal Hybrid RAG</span>
        </div>
      </div>

      {/* Right Tools & Status */}
      <div className="flex items-center gap-3">
        {/* Quick Global Search Trigger */}
        <button
          onClick={onOpenGlobalSearch}
          className="hidden md:flex items-center gap-3 px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-400 hover:text-slate-200 text-xs transition-colors"
        >
          <Search size={14} className="text-slate-400" />
          <span>Search documents or topics...</span>
          <kbd className="px-1.5 py-0.5 text-[10px] bg-slate-900 border border-slate-700 rounded text-slate-300">⌘K</kbd>
        </button>

        {/* Backend Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-white/10 text-xs font-medium">
          <span className={`w-2 h-2 rounded-full ${isBackendLive ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-amber-400 shadow-[0_0_8px_#fbbf24]'}`} />
          <span className="hidden lg:inline text-slate-300">
            {isBackendLive ? 'Knowledge Engine Live' : 'RAG Standby'}
          </span>
        </div>

        {/* Theme Switcher */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications Button */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-cyan-300 transition-colors relative"
            title="Notifications"
          >
            <Bell size={18} />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 bg-[#0d142a]/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl p-4 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <span className="text-xs font-bold text-white uppercase tracking-wider">System Activity</span>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X size={14} />
                </button>
              </div>
              <div className="mt-3 space-y-2.5">
                {notifications.map((n) => (
                  <div key={n.id} className="p-2.5 rounded-xl bg-white/5 border border-white/5 flex items-start gap-2.5">
                    <div className="w-2 h-2 mt-1.5 rounded-full bg-cyan-400 shrink-0" />
                    <div>
                      <p className="text-xs text-slate-200 font-medium">{n.title}</p>
                      <span className="text-[10px] text-slate-400">{n.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
