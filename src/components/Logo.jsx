import React from 'react';

export function Logo({ size = 'md', showTagline = false }) {
  const iconSize = size === 'sm' ? 'w-7 h-7' : size === 'lg' ? 'w-12 h-12' : 'w-9 h-9';
  const textSize = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-3xl' : 'text-xl';

  return (
    <div className="flex items-center gap-3 group select-none">
      {/* V-shaped Geometric Knowledge Node Symbol */}
      <div className={`relative ${iconSize} flex items-center justify-center`}>
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500 via-violet-600 to-magenta-500 rounded-xl blur-md opacity-70 group-hover:opacity-100 transition-opacity duration-300"></div>
        <svg
          className="relative w-full h-full p-1"
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Futuristic V-Node Shape */}
          <path
            d="M8 10L20 32L32 10"
            stroke="url(#vexora-grad-1)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M14 10L20 22L26 10"
            stroke="url(#vexora-grad-2)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Glowing Connected Nodes */}
          <circle cx="8" cy="10" r="3" fill="#00F0FF" className="animate-pulse" />
          <circle cx="32" cy="10" r="3" fill="#F72585" className="animate-pulse" />
          <circle cx="20" cy="32" r="3.5" fill="#9D4EDD" className="animate-pulse" />
          <circle cx="20" cy="22" r="2.5" fill="#FFFFFF" />

          <defs>
            <linearGradient id="vexora-grad-1" x1="8" y1="10" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop stopColor="#00F0FF" />
              <stop offset="0.5" stopColor="#9D4EDD" />
              <stop offset="1" stopColor="#F72585" />
            </linearGradient>
            <linearGradient id="vexora-grad-2" x1="14" y1="10" x2="26" y2="22" gradientUnits="userSpaceOnUse">
              <stop stopColor="#FFFFFF" />
              <stop offset="1" stopColor="#00F0FF" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Brand Text */}
      <div className="flex flex-col">
        <div className={`font-extrabold tracking-wider ${textSize} text-white flex items-center gap-1.5`}>
          <span>VEXORA</span>
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
        </div>
        {showTagline && (
          <span className="text-[10px] tracking-widest text-cyan-400 uppercase font-semibold -mt-0.5">
            Ask. Discover. Verify.
          </span>
        )}
      </div>
    </div>
  );
}
