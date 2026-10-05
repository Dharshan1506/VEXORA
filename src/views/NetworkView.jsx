import React, { useState } from 'react';
import { Network, Database, Layers, Sparkles, Search, Filter, BookOpen } from 'lucide-react';

export function NetworkView() {
  const [selectedNode, setSelectedNode] = useState(null);

  const nodes = [
    { id: 1, name: 'Academic Regulations 2026', type: 'document', category: 'Academic', x: 250, y: 180, r: 24, color: '#00F0FF' },
    { id: 2, name: 'Section 4.2 Attendance', type: 'section', category: 'Academic', x: 420, y: 120, r: 18, color: '#9D4EDD' },
    { id: 3, name: '80% Threshold Policy', type: 'topic', category: 'Rules', x: 600, y: 140, r: 16, color: '#F72585' },
    { id: 4, name: 'Examination Handbook 2026', type: 'document', category: 'Exam', x: 220, y: 340, r: 24, color: '#00F0FF' },
    { id: 5, name: 'Condonation Rules', type: 'topic', category: 'Rules', x: 460, y: 260, r: 16, color: '#F72585' },
    { id: 6, name: 'Hostel Guidelines 2026', type: 'document', category: 'Hostel', x: 180, y: 480, r: 24, color: '#00F0FF' },
    { id: 7, name: 'Curfew & Leave Rules', type: 'topic', category: 'Hostel', x: 400, y: 440, r: 16, color: '#F72585' },
    { id: 8, name: 'Campus Placement Policy', type: 'document', category: 'Placement', x: 580, y: 360, r: 24, color: '#00F0FF' },
    { id: 9, name: 'CGPA Eligibility (7.5+)', type: 'topic', category: 'Placement', x: 750, y: 340, r: 16, color: '#F72585' },
  ];

  const links = [
    { source: 1, target: 2 },
    { source: 2, target: 3 },
    { source: 1, target: 5 },
    { source: 4, target: 5 },
    { source: 6, target: 7 },
    { source: 8, target: 9 },
    { source: 4, target: 2 },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Network size={24} className="text-cyan-400" />
            <span>Interactive Knowledge Graph</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Visual topology mapping relationships between official documents, sections, topics, and policies.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            9 Knowledge Nodes
          </span>
          <span className="px-2.5 py-1 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">
            7 Synaptic Links
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Graph Canvas */}
        <div className="lg:col-span-8 glass-panel p-4 relative min-h-[500px] flex items-center justify-center overflow-hidden">
          <svg className="w-full h-[500px] select-none">
            <defs>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Render Links */}
            {links.map((link, idx) => {
              const sourceNode = nodes.find((n) => n.id === link.source);
              const targetNode = nodes.find((n) => n.id === link.target);
              if (!sourceNode || !targetNode) return null;

              return (
                <line
                  key={idx}
                  x1={sourceNode.x}
                  y1={sourceNode.y}
                  x2={targetNode.x}
                  y2={targetNode.y}
                  stroke="#00F0FF"
                  strokeOpacity="0.3"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                />
              );
            })}

            {/* Render Nodes */}
            {nodes.map((node) => (
              <g
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.r}
                  fill={node.color}
                  fillOpacity="0.25"
                  stroke={node.color}
                  strokeWidth="2"
                  filter="url(#glow)"
                  className="transition-all duration-300 group-hover:r-[28px]"
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={4}
                  fill="#FFFFFF"
                />
                <text
                  x={node.x}
                  y={node.y + node.r + 14}
                  textAnchor="middle"
                  fill="#E2E8F0"
                  fontSize="11"
                  fontWeight="600"
                  className="pointer-events-none"
                >
                  {node.name}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {/* Node Inspector Drawer */}
        <div className="lg:col-span-4 glass-panel p-6 space-y-4">
          <div className="border-b border-white/10 pb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Node Inspector</h3>
          </div>

          {selectedNode ? (
            <div className="space-y-4 animate-in fade-in">
              <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 space-y-2">
                <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase">
                  TYPE: {selectedNode.type}
                </span>
                <h4 className="text-base font-bold text-white">{selectedNode.name}</h4>
                <span className="inline-block px-2 py-0.5 rounded bg-white/10 text-xs text-slate-200">
                  Category: {selectedNode.category}
                </span>
              </div>

              <div className="space-y-2 text-xs text-slate-300">
                <span className="font-bold text-slate-400 block uppercase text-[10px]">Connected Entities</span>
                <ul className="space-y-1 font-mono">
                  {links
                    .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
                    .map((l, idx) => {
                      const otherId = l.source === selectedNode.id ? l.target : l.source;
                      const otherNode = nodes.find((n) => n.id === otherId);
                      return (
                        <li key={idx} className="p-2 rounded bg-slate-900/60 border border-white/5 flex items-center justify-between">
                          <span>{otherNode?.name}</span>
                          <span className="text-[10px] text-cyan-400">{otherNode?.type}</span>
                        </li>
                      );
                    })}
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 space-y-2 text-slate-500">
              <Database size={32} className="mx-auto text-slate-600" />
              <p className="text-xs font-medium">Click any graph node to inspect details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
