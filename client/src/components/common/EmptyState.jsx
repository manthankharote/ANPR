import React from 'react';
import { ShieldAlert } from 'lucide-react';

const EmptyState = ({ title = 'No data available', message = 'There are no records matching your criteria.', icon: Icon = ShieldAlert, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl glass-card">
      <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/50 mb-4 text-slate-400">
        <Icon className="w-10 h-10" />
      </div>
      <h3 className="text-lg font-bold text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm mb-6">{message}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

export default EmptyState;
