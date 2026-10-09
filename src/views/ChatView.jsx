import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send,
  Plus,
  Search,
  Sparkles,
  FileText,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Clock,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';

export function ChatView({
  token,
  pendingQuery,
  onPendingQueryConsumed,
  onUploadClick,
  onViewSource,
}) {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [activeCitation, setActiveCitation] = useState(null);
  const [loadingStep, setLoadingStep] = useState('');
  const [suggestions, setSuggestions] = useState([
    {
      id: 'attendance',
      title: 'Attendance Policy',
      text: 'What is the minimum attendance requirement for semester exams?',
      has_evidence: true,
      badge: 'Policy Query',
    },
    {
      id: 'exam',
      title: 'Internal Exams & Evaluation',
      text: 'What is the weightage of Continuous Internal Assessment and end semester exams?',
      has_evidence: true,
      badge: 'Policy Query',
    },
    {
      id: 'regulations',
      title: 'Academic Regulations',
      text: 'What are the key policy requirements in the uploaded academic regulations?',
      has_evidence: true,
      badge: 'Policy Query',
    },
    {
      id: 'placement',
      title: 'Placement Rules',
      text: 'What CGPA and documents are required for campus placement eligibility?',
      has_evidence: false,
      badge: 'Suggested Query',
    },
  ]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  // ── Load dynamic evidence-aware suggestions ─────────────────────────────────
  useEffect(() => {
    if (!token) return;
    fetch('/api/documents/suggested-queries', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.suggestions?.length > 0) {
          setSuggestions(data.suggestions);
        }
      })
      .catch((e) => console.error('[Chat] Could not load suggested queries:', e));
  }, [token]);

  // ── Load conversation list ──────────────────────────────────────────────────
  const fetchConversations = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/conversations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (e) {
      console.error('[Chat] Could not load conversations:', e);
    }
  }, [token]);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  // ── Load messages for active conversation ───────────────────────────────────
  useEffect(() => {
    if (!activeConversationId || !token) {
      setMessages([]);
      return;
    }
    (async () => {
      try {
        const res = await fetch(`/api/conversations/${activeConversationId}/messages`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setMessages(
            (data.messages || []).map((m) => ({
              role: m.role,
              content: m.content,
              keyInformation: m.key_information,
              evidenceStrength: m.evidence_strength,
              evidenceStatus: m.evidence_status,
              citations: m.citations || [],
              sources: m.sources || [],
            }))
          );
        }
      } catch (e) {
        console.error('[Chat] Could not load messages:', e);
      }
    })();
  }, [activeConversationId, token]);

  // ── Consume pending query from CommandCenter ────────────────────────────────
  useEffect(() => {
    if (pendingQuery) {
      handleSendMessage(pendingQuery);
      onPendingQueryConsumed?.();
    }
  }, [pendingQuery]);

  // ── Send message ────────────────────────────────────────────────────────────
  const handleSendMessage = async (text) => {
    const query = typeof text === 'string' ? text : inputText;
    if (!query.trim() || isLoading) return;
    setInputText('');

    // Optimistically append user message
    setMessages((prev) => [...prev, { role: 'user', content: query }]);
    setIsLoading(true);
    setLoadingStep('Searching university knowledge...');

    try {
      const body = {
        query,
        conversation_id: activeConversationId || undefined,
      };

      setTimeout(() => setLoadingStep('Running BM25 + vector search...'), 800);
      setTimeout(() => setLoadingStep('Applying RRF fusion & cross-encoder reranking...'), 1800);
      setTimeout(() => setLoadingStep('Checking evidence & generating answer...'), 3000);

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Chat API error (${res.status})`);
      }

      const data = await res.json();
      const ans = data.answer;

      // Set conversation id from response if new
      if (!activeConversationId && data.conversation_id) {
        setActiveConversationId(data.conversation_id);
        fetchConversations();
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: ans.content,
          keyInformation: ans.keyInformation,
          evidenceStrength: ans.evidenceStrength,
          evidenceStatus: ans.evidenceStatus,
          citations: ans.citations || [],
          sources: ans.sources || [],
          conflicts: ans.conflicts || [],
          llm_used: ans.llm_used,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error: ${err.message}`,
          evidenceStatus: 'error',
          citations: [],
          sources: [],
        },
      ]);
    } finally {
      setIsLoading(false);
      setLoadingStep('');
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    handleSendMessage(inputText);
  };

  const currentAnswer = messages.filter((m) => m.role === 'assistant').slice(-1)[0];
  const activeSources = currentAnswer?.sources || [];

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden">

      {/* LEFT: Conversation History */}
      <div className="w-64 bg-[#070b19]/90 border-r border-white/10 flex flex-col shrink-0">
        <div className="p-4 space-y-3 border-b border-white/10">
          <button
            onClick={() => { setActiveConversationId(null); setMessages([]); }}
            className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-cyan-500/20 to-violet-600/20 border border-cyan-500/30 text-cyan-300 font-semibold text-xs hover:from-cyan-500/30 hover:to-violet-600/30 transition-all flex items-center justify-center gap-2 shadow-lg"
          >
            <Plus size={16} /> New Conversation
          </button>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={historySearch}
              onChange={(e) => setHistorySearch(e.target.value)}
              placeholder="Search chat history..."
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-2">Recent Sessions</span>
            {conversations
              .filter((c) => c.title.toLowerCase().includes(historySearch.toLowerCase()))
              .map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConversationId(c.id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between group transition-colors ${
                    activeConversationId === c.id
                      ? 'bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/30'
                      : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate max-w-[140px]">{c.title}</span>
                  <span className="text-[9px] text-slate-500">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
          </div>
        </div>
      </div>

      {/* CENTER: Chat Stream */}
      <div className="flex-1 flex flex-col bg-[#070b19]/40 relative overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto space-y-8 my-auto">
              <div className="space-y-3 animate-in fade-in zoom-in-95 duration-300">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-xs font-semibold text-cyan-300">
                  <Sparkles size={14} className="text-cyan-400 animate-pulse" />
                  <span>Evidence-Grounded RAG Engine</span>
                </div>
                <h2 className="text-4xl font-extrabold text-white tracking-tight">
                  Ask. Discover. <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-violet-500">Verify.</span>
                </h2>
                <p className="text-slate-400 text-sm max-w-lg">
                  Search your university's policies using natural language with verifiable citations from uploaded documents.
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                {suggestions.map((item, idx) => {
                  const isVerified = item.has_evidence;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(item.text)}
                      className="glass-panel-interactive p-4 text-left flex items-start gap-3 group relative"
                    >
                      <div
                        className={`p-2 rounded-xl border group-hover:scale-110 transition-transform ${
                          isVerified
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                        }`}
                      >
                        {isVerified ? <ShieldCheck size={18} /> : <Sparkles size={18} />}
                      </div>
                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1.5">
                          <span className="block text-xs font-bold text-white group-hover:text-cyan-300 transition-colors truncate">
                            {item.title}
                          </span>
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                              isVerified
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-white/5 text-slate-400 border border-white/10'
                            }`}
                          >
                            {item.badge || (isVerified ? 'Verified Evidence' : 'Suggested Query')}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{item.text}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-4 max-w-4xl ${msg.role === 'user' ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-lg shadow-cyan-500/20">
                    VX
                  </div>
                )}
                <div className={`space-y-3 ${msg.role === 'user' ? 'max-w-lg' : 'w-full'}`}>
                  {msg.role === 'user' ? (
                    <div className="p-4 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 text-white text-sm font-medium shadow-md">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="glass-panel p-6 space-y-4 border-cyan-500/20 shadow-2xl">

                      {/* Insufficient Evidence Banner */}
                      {msg.evidenceStatus === 'insufficient' && (
                        <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30">
                          <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-bold text-amber-300">⚠ Insufficient Evidence</p>
                            <p className="text-[11px] text-amber-200/80 mt-0.5">
                              No reliable information was found in the uploaded documents for this query.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Answer text */}
                      <div className="text-sm text-slate-200 leading-relaxed font-normal whitespace-pre-line">
                        {msg.content}
                      </div>

                      {/* Key Information */}
                      {msg.keyInformation && msg.evidenceStatus !== 'insufficient' && (
                        <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 space-y-1">
                          <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                            <Sparkles size={12} /> Key Information
                          </span>
                          <p className="text-xs text-cyan-200 font-medium">{msg.keyInformation}</p>
                        </div>
                      )}

                      {/* Evidence Strength Meter */}
                      {msg.evidenceStrength && (
                        <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {msg.evidenceStatus === 'insufficient'
                              ? <AlertCircle size={16} className="text-amber-400" />
                              : <ShieldCheck size={16} className="text-emerald-400" />
                            }
                            <span className="text-xs font-semibold text-slate-300">Evidence:</span>
                            <span className={`text-xs font-bold ${
                              msg.evidenceStatus === 'insufficient' ? 'text-amber-400' : 'text-emerald-400'
                            }`}>{msg.evidenceStrength}</span>
                          </div>
                          <div className="w-32 h-2 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                msg.evidenceStatus === 'insufficient'
                                  ? 'bg-amber-500'
                                  : 'bg-gradient-to-r from-cyan-400 to-emerald-400'
                              }`}
                              style={{
                                width: msg.evidenceStrength?.includes('Strong')
                                  ? '90%'
                                  : msg.evidenceStrength?.includes('Retrieved')
                                  ? '65%'
                                  : '25%',
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* RAG Pipeline Transparency */}
                      {msg.evidenceStatus === 'sufficient' && (
                        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-white/5 flex flex-wrap gap-2 text-[10px] text-slate-500">
                          <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-emerald-500" /> BM25 search</span>
                          <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-emerald-500" /> Vector search</span>
                          <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-emerald-500" /> RRF fusion</span>
                          <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-emerald-500" /> Cross-encoder reranking</span>
                          <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-emerald-500" /> Evidence Guard</span>
                          {msg.llm_used && (
                            <span className="flex items-center gap-1"><CheckCircle2 size={10} className="text-violet-400" /> Gemini LLM synthesis</span>
                          )}
                        </div>
                      )}

                      {/* Citations */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="pt-2 border-t border-white/10 flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-bold text-slate-400 uppercase">Citations:</span>
                          {msg.citations.map((c, i) => (
                            <button
                              key={i}
                              onClick={() => { setActiveCitation(c); if (onViewSource) onViewSource(c); }}
                              className="citation-tag"
                            >
                              <span>[{c.id}]</span>
                              <span>{c.docName}{c.page != null ? ` (p.${c.page})` : ''}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-center gap-3 p-4 rounded-2xl glass-panel border-cyan-500/30 max-w-md animate-pulse">
              <div className="w-7 h-7 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-300">
                <Sparkles size={16} className="animate-spin" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-cyan-300">VEXORA RAG Engine Active...</p>
                <p className="text-[11px] text-slate-400">{loadingStep}</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="p-4 bg-[#070b19]/80 border-t border-white/10 backdrop-blur-xl">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative flex items-center gap-2">
            <button
              type="button"
              onClick={onUploadClick}
              className="p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-cyan-300 transition-colors"
              title="Upload Document to Vault"
            >
              <Plus size={18} />
            </button>
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask VEXORA about attendance rules, exam dates, hostel policies..."
                className="w-full py-3.5 pl-4 pr-12 rounded-xl bg-slate-900/90 border border-white/10 text-white placeholder-slate-400 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-cyan-500/20"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>

      {/* RIGHT: Evidence Panel */}
      <div className="w-80 bg-[#070b19]/90 border-l border-white/10 flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-cyan-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Grounding Evidence</h3>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            {activeSources.length} Sources
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeSources.length === 0 ? (
            <div className="text-center py-12 space-y-3 text-slate-500">
              <BookOpen size={28} className="mx-auto text-slate-600" />
              <p className="text-xs font-medium">No active evidence.</p>
              <p className="text-[11px] text-slate-600 max-w-[180px] mx-auto">
                Ask a question to see retrieved document sections here.
              </p>
            </div>
          ) : (
            activeSources.map((source, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl glass-panel space-y-2 border transition-all ${
                  activeCitation?.id === source.citationId
                    ? 'border-cyan-400 bg-cyan-500/10 shadow-lg shadow-cyan-500/20'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                    Source {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {source.page != null ? `Page ${source.page}` : 'Page N/A'}
                  </span>
                </div>

                <h4 className="text-xs font-bold text-white leading-snug">{source.docName}</h4>

                {source.section && (
                  <span className="text-[11px] font-semibold text-cyan-400 block">{source.section}</span>
                )}

                <p className="text-[11px] text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-white/5 font-mono leading-relaxed italic">
                  "{source.snippet}"
                </p>

                <div className="pt-1 flex items-center justify-between text-[11px]">
                  <div className="space-y-0.5">
                    <span className="text-slate-500 font-mono block">
                      Score: {(source.score * 100).toFixed(0)}%
                    </span>
                    {source.bm25_rank && (
                      <span className="text-slate-600 font-mono text-[10px] block">
                        BM25 #{source.bm25_rank} · Vec #{source.vector_rank || '—'}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => onViewSource && onViewSource(source)}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                  >
                    View <ExternalLink size={12} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
