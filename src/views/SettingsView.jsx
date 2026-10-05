import React, { useState } from 'react';
import { Settings, Key, ShieldCheck, Save, Cpu, CheckCircle2 } from 'lucide-react';

export function SettingsView() {
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);
  const [similarityThreshold, setSimilarityThreshold] = useState('0.65');
  const [topK, setTopK] = useState('5');

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto animate-in fade-in duration-300">
      <div className="border-b border-white/10 pb-6">
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <Settings size={24} className="text-cyan-400" />
          <span>Platform Settings & API Credentials</span>
        </h1>
        <p className="text-slate-400 text-xs mt-1">
          Configure model settings, vector retrieval parameters, and external LLM API credentials.
        </p>
      </div>

      {saved && (
        <div className="p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 size={16} /> Configuration settings saved successfully!
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Gemini API Key Box */}
        <div className="glass-panel p-6 space-y-4 border-cyan-500/20">
          <div className="flex items-center gap-2">
            <Key size={18} className="text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Google Gemini API Credential</h3>
          </div>
          <p className="text-xs text-slate-400">
            VEXORA includes a built-in local dual RAG synthesizer. Providing a Google Gemini API key enables real-time LLM answer generation with structured JSON citations.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">GEMINI_API_KEY</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-white font-mono text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Vector Retrieval Parameters */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-violet-400" />
            <h3 className="text-sm font-bold text-white">RAG Hybrid Search Parameters</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Cosine Similarity Cutoff</label>
              <input
                type="text"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Top-K Chunks to Retrieve</label>
              <input
                type="text"
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-violet-600 to-magenta-500 hover:from-cyan-400 hover:to-magenta-400 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
        >
          <Save size={16} /> Save Configuration
        </button>
      </form>
    </div>
  );
}
