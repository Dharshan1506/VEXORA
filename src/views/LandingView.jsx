import React, { useState } from 'react';
import { Logo } from '../components/Logo';
import { Sparkles, ShieldCheck, Cpu, Database, ArrowRight, Lock, Mail, User, Key, CheckCircle2 } from 'lucide-react';

export function LandingView({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('scholar@university.edu');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('Dr. Alex Mercer');
  const [role, setRole] = useState('Professor & Researcher');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      const body = isRegister
        ? { name, email, password, role }
        : { email, password };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Authentication failed. Please try again.');
        return;
      }
      onLogin(data.user, data.token);
    } catch (err) {
      setError('Cannot connect to server. Ensure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (demoRole) => {
    setError('');
    setLoading(true);
    const creds = demoRole === 'admin'
      ? { email: 'admin@vexora.edu', password: 'Admin@2026' }
      : { email: 'student@vexora.edu', password: 'Student@2026' };
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Demo login failed.'); return; }
      onLogin(data.user, data.token);
    } catch {
      setError('Backend unreachable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 overflow-hidden">
      {/* Dynamic Ambient Glows */}
      <div className="absolute top-1/4 left-1/6 w-96 h-96 bg-cyan-500/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/6 w-96 h-96 bg-violet-600/20 rounded-full blur-[140px] pointer-events-none" />

      <div className="relative z-10 w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column: Branding & Value Proposition */}
        <div className="lg:col-span-7 space-y-8">
          <Logo size="lg" showTagline={true} />

          <div className="space-y-4">
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white leading-tight tracking-tight">
              Your University’s Knowledge, <br />
              <span className="text-gradient-cyan">One Intelligent Layer.</span>
            </h1>
            <p className="text-slate-300 text-lg max-w-xl font-normal leading-relaxed">
              VEXORA unifies academic regulations, exam schedules, policy manuals, and research catalogs into a high-precision, evidence-grounded multimodal RAG platform.
            </p>
          </div>

          {/* Feature Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {[
              { title: 'Multimodal Knowledge', desc: 'PDF, DOCX, PPTX & Scanned Image OCR', icon: Cpu, color: 'text-cyan-400' },
              { title: 'Evidence-Grounded', desc: 'Zero hallucinated claims with source verification', icon: ShieldCheck, color: 'text-emerald-400' },
              { title: 'Hybrid Retrieval', desc: 'Dense vector search + BM25 keyword reranking', icon: Database, color: 'text-violet-400' },
              { title: 'Source Citations', desc: 'Direct page & section deep-linking references', icon: Sparkles, color: 'text-magenta-400' },
            ].map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md flex items-start gap-3.5">
                  <div className={`p-2.5 rounded-xl bg-white/5 ${f.color}`}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{f.title}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{f.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Demo Login Badges */}
          <div className="pt-4 flex items-center gap-3">
            <span className="text-xs text-slate-400 font-medium">Quick Demo Login:</span>
            <button
              onClick={() => handleDemoLogin('student')}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-xs font-semibold text-cyan-300 transition-colors flex items-center gap-1.5"
            >
              <CheckCircle2 size={14} /> Student Demo
            </button>
            <button
              onClick={() => handleDemoLogin('admin')}
              className="px-3.5 py-1.5 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/30 text-xs font-semibold text-violet-300 transition-colors flex items-center gap-1.5"
            >
              <ShieldCheck size={14} /> Admin Demo
            </button>
          </div>
        </div>

        {/* Right Column: Glass Login Panel */}
        <div className="lg:col-span-5">
          <div className="glass-panel p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-cyan-500/20 rounded-full blur-2xl pointer-events-none" />

            <div className="mb-6 text-center">
              <h2 className="text-2xl font-bold text-white">
                {isRegister ? 'Join VEXORA' : 'Welcome Back'}
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                {isRegister ? 'Access your institution’s knowledge ecosystem' : 'Authenticate to query university intelligence'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Full Name</label>
                    <div className="relative">
                      <User size={16} className="absolute left-3 top-3 text-slate-500" />
                      <input
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Dr. Alex Mercer"
                        className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-white/10 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Role / Designation</label>
                    <input
                      type="text"
                      required
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      placeholder="Professor / Student"
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-900/60 border border-white/10 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">University Email</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-3 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="user@university.edu"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-white/10 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-900/60 border border-white/10 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  />
                </div>
              </div>

              {/* Error message */}
              {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-violet-600 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 text-white font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2 group mt-2 disabled:opacity-60"
              >
                <span>{loading ? 'Authenticating...' : (isRegister ? 'Create Account' : 'Enter VEXORA Platform')}</span>
                {!loading && <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-white/10 text-center">
              <button
                onClick={() => setIsRegister(!isRegister)}
                className="text-xs text-slate-400 hover:text-cyan-300 font-medium transition-colors"
              >
                {isRegister ? 'Already registered? Sign in' : "Don't have an account? Create one"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
