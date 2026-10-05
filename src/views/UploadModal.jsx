import React, { useState } from 'react';
import { Upload, X, CheckCircle2, Loader2, FileText, AlertCircle, Sparkles } from 'lucide-react';

export function UploadModal({ isOpen, onClose, onUploadComplete, token }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [category, setCategory] = useState('Academic');
  const [version, setVersion] = useState('v1.0');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [error, setError] = useState(null);
  const [uploadStats, setUploadStats] = useState(null);

  if (!isOpen) return null;

  const pipelineStages = [
    { label: 'UPLOAD',  desc: 'Sending document to VEXORA server' },
    { label: 'EXTRACT', desc: 'Extracting text from document structure' },
    { label: 'OCR',     desc: 'Running OCR on image-based pages (if needed)' },
    { label: 'CHUNK',   desc: 'Splitting into contextual sliding-window chunks' },
    { label: 'EMBED',   desc: 'Computing dense vector embeddings' },
    { label: 'INDEX',   desc: 'Writing to BM25 index & vector store' },
    { label: 'READY',   desc: 'Document indexed and searchable in VEXORA' },
  ];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setUploadStats(null);
      setCurrentStep(-1);
    }
  };

  const handleStartIngestion = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setError(null);
    setCurrentStep(0); // UPLOAD

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', category);
      formData.append('version', version);

      setCurrentStep(1); // EXTRACT

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      // Advance stages visually while waiting for backend to finish
      // (real work happens synchronously on the backend)
      const stageDelay = (ms) => new Promise((r) => setTimeout(r, ms));

      setCurrentStep(2); // OCR
      await stageDelay(400);
      setCurrentStep(3); // CHUNK
      await stageDelay(300);
      setCurrentStep(4); // EMBED
      await stageDelay(400);
      setCurrentStep(5); // INDEX
      await stageDelay(300);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed (HTTP ${response.status})`);
      }

      const data = await response.json();
      setCurrentStep(6); // READY
      await stageDelay(500);

      setUploadStats(data.stats);
      onUploadComplete(data.document);

      // Close after showing the READY state briefly
      await stageDelay(800);
      setIsProcessing(false);
      setSelectedFile(null);
      setCurrentStep(-1);
      onClose();

    } catch (err) {
      setIsProcessing(false);
      setCurrentStep(-1);
      setError(err.message || 'Upload failed. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-2xl p-6 space-y-6 relative shadow-2xl border-cyan-500/30 overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Upload size={20} className="text-cyan-400" />
            <h2 className="text-lg font-bold text-white">Add Knowledge to VEXORA</h2>
          </div>
          <button
            onClick={() => { if (!isProcessing) { setSelectedFile(null); setError(null); onClose(); } }}
            className="p-1 rounded-lg text-slate-400 hover:text-white disabled:opacity-30"
            disabled={isProcessing}
          >
            <X size={18} />
          </button>
        </div>

        {!isProcessing ? (
          <div className="space-y-4">
            {/* Drag & Drop Area */}
            <div className="relative p-8 rounded-2xl border-2 border-dashed border-cyan-500/40 bg-slate-900/60 hover:bg-slate-900/90 hover:border-cyan-400 transition-all text-center group cursor-pointer">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.docx,.pptx,.txt,.png,.jpg,.jpeg,.webp"
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <div className="space-y-3 pointer-events-none">
                <div className="w-12 h-12 mx-auto rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <FileText size={24} />
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-bold text-cyan-300">{selectedFile.name}</p>
                    <span className="text-xs text-slate-400 font-mono">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-bold text-white">Drag & drop university document here</p>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports PDF, DOCX, PPTX, TXT, PNG, JPG, WEBP (up to 50 MB)
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Error display */}
            {error && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Metadata Controls */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Knowledge Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value="Academic">Academic</option>
                  <option value="Examination">Examination</option>
                  <option value="Hostel">Hostel</option>
                  <option value="Placement">Placement</option>
                  <option value="Rules">Rules & Regulations</option>
                  <option value="General">General Notice</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Document Version Tag</label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="v1.0"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleStartIngestion}
              disabled={!selectedFile}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-violet-600 to-fuchsia-600 hover:from-cyan-400 hover:to-fuchsia-500 disabled:opacity-50 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition-all"
            >
              Start Ingestion Pipeline
            </button>
          </div>
        ) : (
          /* Processing Pipeline View */
          <div className="space-y-6 py-4">
            <div className="text-center space-y-2">
              <Sparkles size={28} className="mx-auto text-cyan-400 animate-spin" />
              <h3 className="text-base font-bold text-white">Processing Document...</h3>
              <p className="text-xs text-slate-400">{selectedFile?.name}</p>
            </div>

            {/* Stage Indicators */}
            <div className="space-y-2.5 bg-slate-950/60 p-4 rounded-2xl border border-white/5">
              {pipelineStages.map((stage, idx) => {
                const isCompleted = idx < currentStep;
                const isCurrent = idx === currentStep;

                return (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      {isCompleted ? (
                        <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 size={16} className="text-cyan-400 animate-spin shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0" />
                      )}
                      <span className={`font-mono font-bold ${isCompleted ? 'text-emerald-300' : isCurrent ? 'text-cyan-300' : 'text-slate-500'}`}>
                        {stage.label}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 truncate max-w-[240px]">{stage.desc}</span>
                  </div>
                );
              })}
            </div>

            {/* Backend is doing real work note */}
            <p className="text-center text-[11px] text-slate-500">
              The backend is extracting text, generating embeddings, and building the index.
              This may take 10–60 seconds depending on document size.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
