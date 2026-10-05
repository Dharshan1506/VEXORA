import React from 'react';
import { Logo } from './Logo';
import {
  LayoutDashboard,
  MessageSquare,
  FolderKanban,
  FileText,
  GitCompare,
  AlertTriangle,
  Network,
  BarChart3,
  ShieldAlert,
  Settings,
  HelpCircle,
  LogOut,
  ChevronLeft,
  ChevronRight,
  UserCheck
} from 'lucide-react';

export function Sidebar({ currentView, setCurrentView, isCollapsed, setIsCollapsed, user, onLogout }) {
  const mainNav = [
    { id: 'command', label: 'Command Center', icon: LayoutDashboard },
    { id: 'chat', label: 'Ask VEXORA', icon: MessageSquare, badge: 'RAG' },
    { id: 'vault', label: 'Knowledge Vault', icon: FolderKanban },
    { id: 'viewer', label: 'Document Viewer', icon: FileText },
    { id: 'compare', label: 'Policy Compare', icon: GitCompare },
    { id: 'conflict', label: 'Conflict Detector', icon: AlertTriangle, badge: 'AI' },
    { id: 'network', label: 'Knowledge Graph', icon: Network },
    { id: 'insights', label: 'Insights & Analytics', icon: BarChart3 },
    { id: 'admin', label: 'Admin Panel', icon: ShieldAlert },
  ];

  return (
    <aside
      className={`relative z-20 h-screen bg-[#070b19]/80 backdrop-blur-2xl border-r border-white/10 transition-all duration-300 flex flex-col justify-between ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Header & Collapse Toggle */}
      <div className="p-4 flex items-center justify-between border-b border-white/5">
        {!isCollapsed ? (
          <Logo size="md" showTagline={true} />
        ) : (
          <div className="mx-auto">
            <Logo size="sm" showTagline={false} />
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors border border-white/10"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Main Navigation List */}
      <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          {!isCollapsed && 'Navigation'}
        </div>
        {mainNav.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-violet-600/20 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-white/5 border border-transparent'
              }`}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon
                size={20}
                className={`transition-transform duration-200 ${
                  isActive ? 'text-cyan-400 scale-110' : 'text-slate-400 group-hover:text-cyan-300'
                }`}
              />
              {!isCollapsed && <span className="truncate">{item.label}</span>}
              {!isCollapsed && item.badge && (
                <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Profile & Settings */}
      <div className="p-3 border-t border-white/10 space-y-2 bg-slate-950/40">
        <button
          onClick={() => setCurrentView('settings')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors ${
            currentView === 'settings' ? 'bg-white/10 text-white' : ''
          }`}
          title={isCollapsed ? 'Settings' : undefined}
        >
          <Settings size={18} />
          {!isCollapsed && <span>Settings & API</span>}
        </button>

        {/* User Card */}
        <div className="pt-2 flex items-center justify-between gap-2 px-2">
          {!isCollapsed ? (
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold text-xs ring-2 ring-cyan-500/30">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-slate-200 truncate">{user?.name || 'Academic User'}</span>
                <span className="text-[10px] text-cyan-400 truncate">{user?.role || 'University Scholar'}</span>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold text-xs mx-auto">
              {user?.name?.charAt(0) || 'U'}
            </div>
          )}

          {!isCollapsed && (
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
