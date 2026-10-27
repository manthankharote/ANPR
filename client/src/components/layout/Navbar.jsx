import React, { useState, useEffect } from 'react';
import { Bell, ShieldCheck, Activity, Clock } from 'lucide-react';

const Navbar = ({ signalState = 'GREEN' }) => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#0b0f19]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20">
      {/* Left: System Status & Time */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
          <Clock className="w-4 h-4 text-blue-400" />
          <span className="font-mono text-slate-200">{time}</span>
        </div>

        <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs">
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400">Node:</span>
          <span className="font-bold text-white">Central Junction #04</span>
        </div>
      </div>

      {/* Right: Traffic Signal Status & User Badges */}
      <div className="flex items-center space-x-4">
        {/* Signal HUD badge */}
        <div
          className={`flex items-center space-x-2 px-3.5 py-1 rounded-full border text-xs font-extrabold tracking-wide uppercase transition-all ${
            signalState === 'RED'
              ? 'bg-rose-500/15 text-rose-400 border-rose-500/40 shadow-sm shadow-rose-500/20'
              : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/20'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              signalState === 'RED' ? 'bg-rose-500 animate-ping' : 'bg-emerald-500'
            }`}
          />
          <span>SIGNAL: {signalState}</span>
        </div>

        <div className="h-4 w-[1px] bg-slate-800" />

        <div className="flex items-center space-x-2 text-xs font-medium text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="hidden sm:inline">VAHAN Synchronized</span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
