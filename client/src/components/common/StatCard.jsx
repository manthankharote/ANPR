import React from 'react';

const StatCard = ({ title, value, icon: Icon, trend, subtext, color = 'blue' }) => {
  const colorMap = {
    blue: {
      border: 'hover:border-blue-500/40',
      bg: 'bg-blue-500/10 text-blue-400',
      glow: 'shadow-glow-blue',
    },
    red: {
      border: 'hover:border-rose-500/40',
      bg: 'bg-rose-500/10 text-rose-400',
      glow: 'shadow-glow-red',
    },
    amber: {
      border: 'hover:border-amber-500/40',
      bg: 'bg-amber-500/10 text-amber-400',
      glow: 'shadow-glow-amber',
    },
    green: {
      border: 'hover:border-emerald-500/40',
      bg: 'bg-emerald-500/10 text-emerald-400',
      glow: 'shadow-glow-green',
    },
    purple: {
      border: 'hover:border-purple-500/40',
      bg: 'bg-purple-500/10 text-purple-400',
      glow: 'shadow-glow-purple',
    },
  };

  const selected = colorMap[color] || colorMap.blue;

  return (
    <div
      className={`glass-card rounded-2xl p-6 transition-all duration-300 relative overflow-hidden group ${selected.border}`}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-bold tracking-wider uppercase text-slate-400">{title}</span>
        <div className={`p-3 rounded-xl ${selected.bg} transition-transform duration-300 group-hover:scale-110`}>
          {Icon && <Icon className="w-5 h-5" />}
        </div>
      </div>

      <div className="flex items-baseline space-x-2">
        <div className="text-3xl font-extrabold text-white tracking-tight">{value}</div>
        {trend && (
          <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
            {trend}
          </span>
        )}
      </div>

      {subtext && <div className="mt-2 text-xs text-slate-400">{subtext}</div>}

      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:via-white/20" />
    </div>
  );
};

export default StatCard;
