import React, { useState, useEffect } from 'react';
import { Background3D } from './components/Background3D';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { LandingView } from './views/LandingView';
import { CommandCenterView } from './views/CommandCenterView';
import { ChatView } from './views/ChatView';
import { VaultView } from './views/VaultView';
import { UploadModal } from './views/UploadModal';
import { DocumentViewer } from './views/DocumentViewer';
import { CompareView } from './views/CompareView';
import { ConflictView } from './views/ConflictView';
import { NetworkView } from './views/NetworkView';
import { InsightsView } from './views/InsightsView';
import { AdminView } from './views/AdminView';
import { SettingsView } from './views/SettingsView';

export default function App() {
  // ─── Auth state ─────────────────────────────────────────────────────────────
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // ─── UI state ────────────────────────────────────────────────────────────────
  const [currentView, setCurrentView] = useState('command');
  const [theme, setTheme] = useState('dark');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [isBackendLive, setIsBackendLive] = useState(true);

  // Real documents from API (no hardcoded mock)
  const [documents, setDocuments] = useState([]);

  // Pending query from CommandCenter → ChatView
  const [pendingQuery, setPendingQuery] = useState(null);

  // ─── Restore session from localStorage on first load ─────────────────────────
  useEffect(() => {
    const savedToken = localStorage.getItem('vexora_token');
    const savedUser = localStorage.getItem('vexora_user');
    if (savedToken && savedUser) {
      try {
        const u = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(u);
      } catch {
        localStorage.removeItem('vexora_token');
        localStorage.removeItem('vexora_user');
      }
    }
    setAuthChecked(true);
  }, []);

  // ─── Backend health check ─────────────────────────────────────────────────────
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setIsBackendLive(data.status === 'ok'))
      .catch(() => setIsBackendLive(false));
  }, []);

  // ─── Load real documents from API when logged in ──────────────────────────────
  useEffect(() => {
    if (!token) return;
    fetch('/api/documents', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.ok ? res.json() : { documents: [] })
      .then(data => setDocuments(data.documents || []))
      .catch(() => setDocuments([]));
  }, [token, isUploadOpen]); // re-fetch after upload modal closes

  // ─── Auth handlers ────────────────────────────────────────────────────────────
  const handleLogin = (userData, tok) => {
    setUser(userData);
    setToken(tok);
    localStorage.setItem('vexora_token', tok);
    localStorage.setItem('vexora_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('vexora_token');
    localStorage.removeItem('vexora_user');
    setCurrentView('command');
    setDocuments([]);
  };

  // ─── Document handlers ────────────────────────────────────────────────────────
  const handleUploadComplete = (newDoc) => {
    setDocuments(prev => [newDoc, ...prev]);
  };

  const handleDeleteDocument = async (id) => {
    try {
      await fetch(`/api/documents/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      setDocuments(prev => prev.filter(d => d.id !== id));
    } catch (e) {
      console.error('Delete failed:', e);
    }
  };

  // ─── While checking stored auth, render nothing to avoid flash ────────────────
  if (!authChecked) return null;

  // ─── Not authenticated → show landing/login ───────────────────────────────────
  if (!user) {
    return <LandingView onLogin={handleLogin} />;
  }

  // ─── Authenticated app ────────────────────────────────────────────────────────
  return (
    <div className={`min-h-screen bg-[#070b19] text-slate-100 font-sans ${theme}`}>
      {/* 3D Knowledge Core / Particle Background */}
      <Background3D />

      <div className="relative z-10 flex h-screen overflow-hidden">
        {/* Collapsible Sidebar */}
        <Sidebar
          currentView={currentView}
          setCurrentView={setCurrentView}
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
          user={user}
          onLogout={handleLogout}
        />

        {/* Main Content Workspace */}
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
          <Header
            currentView={currentView}
            theme={theme}
            setTheme={setTheme}
            onOpenGlobalSearch={() => setCurrentView('vault')}
            isBackendLive={isBackendLive}
            documents={documents}
          />

          <main className="flex-1 overflow-y-auto">
            {currentView === 'command' && (
              <CommandCenterView
                user={user}
                documents={documents}
                onNavigate={setCurrentView}
                onUploadClick={() => setIsUploadOpen(true)}
                onSearchQuery={(q) => {
                  setCurrentView('chat');
                  setPendingQuery(q);
                }}
              />
            )}

            {currentView === 'chat' && (
              <ChatView
                token={token}
                pendingQuery={pendingQuery}
                onPendingQueryConsumed={() => setPendingQuery(null)}
                onUploadClick={() => setIsUploadOpen(true)}
                onViewSource={(s) => {
                  // Attempt to match source doc to open it
                  const matched = documents.find(d => d.id === s?.documentId) || documents[0] || null;
                  setSelectedDoc(matched);
                  if (matched) setCurrentView('viewer');
                }}
              />
            )}

            {currentView === 'vault' && (
              <VaultView
                documents={documents}
                onUploadClick={() => setIsUploadOpen(true)}
                onViewDocument={(doc) => {
                  setSelectedDoc(doc);
                  setCurrentView('viewer');
                }}
                onCompareDocument={(doc) => {
                  setSelectedDoc(doc);
                  setCurrentView('compare');
                }}
                onDeleteDocument={handleDeleteDocument}
              />
            )}

            {currentView === 'viewer' && (
              <DocumentViewer
                document={selectedDoc || documents[0]}
                token={token}
                onAskAboutDoc={(docName) => {
                  setCurrentView('chat');
                  setPendingQuery(`What are the key policy requirements in ${docName}?`);
                }}
              />
            )}

            {currentView === 'compare' && (
              <CompareView
                documents={documents}
                token={token}
                initialDoc={selectedDoc}
              />
            )}
            {currentView === 'conflict' && <ConflictView token={token} />}
            {currentView === 'network' && <NetworkView />}
            {currentView === 'insights' && <InsightsView />}
            {currentView === 'admin' && (
              <AdminView documents={documents} onDeleteDocument={handleDeleteDocument} />
            )}
            {currentView === 'settings' && <SettingsView />}
          </main>
        </div>
      </div>

      {/* Document Upload Pipeline Modal — real backend upload */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => {
          setIsUploadOpen(false);
          // Refresh document list after modal closes
          if (token) {
            fetch('/api/documents', { headers: { Authorization: `Bearer ${token}` } })
              .then(r => r.ok ? r.json() : { documents: [] })
              .then(d => setDocuments(d.documents || []))
              .catch(() => {});
          }
        }}
        onUploadComplete={handleUploadComplete}
        token={token}
      />
    </div>
  );
}
