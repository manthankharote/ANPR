export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
export const STORAGE_URL = import.meta.env.VITE_STORAGE_URL || 'http://localhost:5000';

export const VIOLATION_TYPES = [
  'Red Light Jump',
  'Over-Speeding',
  'No Helmet',
  'Triple Riding',
  'Wrong-Lane / Wrong-Way Driving',
  'Mobile Phone Usage',
];

export const VIOLATION_COLORS = {
  'Red Light Jump': 'bg-red-500/20 text-red-400 border-red-500/30',
  'Over-Speeding': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'No Helmet': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'Triple Riding': 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  'Wrong-Lane / Wrong-Way Driving': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'Mobile Phone Usage': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
};

export const DEFAULT_FINES = {
  'Red Light Jump': 1000,
  'Over-Speeding': 2000,
  'No Helmet': 1000,
  'Triple Riding': 1000,
  'Mobile Phone Usage': 1500,
  'Wrong-Lane / Wrong-Way Driving': 1500,
  'Expired Insurance': 2000,
  'Expired PUC': 1000,
};
