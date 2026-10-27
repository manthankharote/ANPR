import React, { useState, useEffect } from 'react';
import {
  FolderArchive,
  Search,
  Download,
  ExternalLink,
  ShieldAlert,
  Camera,
  Calendar,
  Eye,
  FileCheck,
} from 'lucide-react';
import { violationService } from '../services/violationService';
import { STORAGE_URL, VIOLATION_COLORS } from '../utils/constants';

const SAMPLE_EVIDENCE = [
  {
    id: 1261,
    plate_number: 'KA03MJ4321',
    violation_type: 'No Helmet',
    timestamp: '2026-10-26 18:42:10',
    total_fine: 4000,
    camera_id: 'Surveillance Cam #04 Junction',
    details: 'Rider operating two-wheeler without protective helmet',
  },
  {
    id: 1260,
    plate_number: 'MH14GH4321',
    violation_type: 'No Helmet',
    timestamp: '2026-10-26 18:35:45',
    total_fine: 1000,
    camera_id: 'Surveillance Cam #04 Junction',
    details: 'Rider operating two-wheeler without protective helmet',
  },
  {
    id: 1259,
    plate_number: 'DL01AB5555',
    violation_type: 'Red Light Jump',
    timestamp: '2026-10-26 18:22:18',
    total_fine: 2000,
    camera_id: 'Surveillance Cam #04 Junction',
    details: 'Crossed Stop Line (Y=480) during active RED signal',
  },
  {
    id: 1258,
    plate_number: 'MH12XY9876',
    violation_type: 'Over-Speeding',
    timestamp: '2026-10-26 18:10:04',
    total_fine: 4000,
    camera_id: 'Surveillance Cam #04 Junction',
    details: 'Speed Gate measurement: 72.4 km/h (Limit: 50.0 km/h)',
  },
];

const Evidence = () => {
  const [evidenceList, setEvidenceList] = useState(SAMPLE_EVIDENCE);
  const [selectedItem, setSelectedItem] = useState(SAMPLE_EVIDENCE[0]);
  const [filterPlate, setFilterPlate] = useState('');

  useEffect(() => {
    const fetchEvidence = async () => {
      try {
        const res = await violationService.getViolations({ limit: 50 });
        if (res.data?.length) {
          setEvidenceList(res.data);
          setSelectedItem(res.data[0]);
        }
      } catch (e) {
        // Fallback
      }
    };
    fetchEvidence();
  }, []);

  const filtered = evidenceList.filter((item) => {
    const clean = filterPlate.replace(/\s+/g, '').toUpperCase();
    return !clean || item.plate_number.includes(clean);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Forensic Evidence Archive</h1>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident photographic evidence snapshots with plate insets and statutory watermarks.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-card rounded-2xl p-4 flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={filterPlate}
            onChange={(e) => setFilterPlate(e.target.value)}
            placeholder="Search evidence by registration plate (e.g., KA03MJ4321, DL01AB5555)..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-xs text-white placeholder-slate-500 font-mono uppercase"
          />
        </div>
      </div>

      {/* Main Evidence Viewer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
        {/* Left: Forensic Snapshot Preview Stage (7 cols) */}
        <div className="lg:col-span-7 glass-card rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <Camera className="w-5 h-5 text-blue-400" />
              <div>
                <h2 className="text-sm font-bold text-white">
                  Forensic Capture #E-CH-2026-{selectedItem?.id}
                </h2>
                <p className="text-xs text-slate-400 font-mono">{selectedItem?.camera_id || 'Cam #04'}</p>
              </div>
            </div>

            <span className="font-mono text-xs font-bold bg-white text-slate-900 px-2.5 py-1 rounded border border-black shadow-sm">
              {selectedItem?.plate_number}
            </span>
          </div>

          {/* High-Resolution Forensic Snapshot Card */}
          <div className="relative aspect-video rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex flex-col justify-between p-4 shadow-2xl">
            {/* Real Snapshot Image if Available */}
            {selectedItem?.snapshot_path && (
              <img
                src={
                  selectedItem.snapshot_path.startsWith('http')
                    ? selectedItem.snapshot_path
                    : `${STORAGE_URL}/evidence/${selectedItem.snapshot_path.replace(/\\/g, '/').split('/').pop()}`
                }
                alt="Forensic Evidence Capture"
                className="absolute inset-0 w-full h-full object-cover"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}

            {/* Top Right Zoomed Plate Picture-in-Picture */}
            <div className="self-end z-10 bg-black/90 p-2 rounded-lg border-2 border-white/80 shadow-xl flex flex-col items-center">
              <div className="w-36 h-12 bg-white rounded flex items-center justify-center border border-black px-2">
                <span className="font-mono font-black text-slate-950 text-sm tracking-wider">
                  {selectedItem?.plate_number}
                </span>
              </div>
              <span className="text-[10px] font-bold text-amber-400 mt-1 uppercase tracking-wider">
                ● Plate ROI Zoom
              </span>
            </div>

            {/* Center Bounding Box Representation */}
            <div className="my-auto mx-auto border-2 border-dashed border-red-500/80 bg-red-500/10 p-6 rounded-lg text-center backdrop-blur-xs z-10">
              <span className="text-xs font-bold text-red-400 uppercase tracking-widest block mb-1">
                [ AI VIOLATOR BOUNDING BOX ]
              </span>
              <p className="text-white font-extrabold text-sm">{selectedItem?.violation_type}</p>
              <span className="text-[11px] text-slate-400 font-mono">
                Tracking ID #{selectedItem?.id}
              </span>
            </div>

            {/* Bottom Statutory Evidence Watermark Banner */}
            <div className="z-10 bg-slate-950/95 border-t border-red-500 p-3 rounded-lg text-slate-300 font-mono text-[11px] space-y-1">
              <div className="flex flex-wrap items-center justify-between text-amber-400 font-bold">
                <span>VIOLATION: {selectedItem?.violation_type?.toUpperCase()}</span>
                <span>CHALLAN: ₹{selectedItem?.total_fine}</span>
              </div>
              <div className="flex flex-wrap items-center justify-between text-slate-400 text-[10px]">
                <span>TIMESTAMP: {selectedItem?.timestamp}</span>
                <span>STATUS: E-CHALLAN STATUTORY RECORD</span>
              </div>
            </div>
          </div>

          {/* Detail Metadata List */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
            <span className="text-slate-400 font-bold block">Audit Evidence Description:</span>
            <p className="text-slate-300 font-mono">{selectedItem?.details}</p>
          </div>
        </div>

        {/* Right: Evidence Archive Selector (3 cols) */}
        <div className="lg:col-span-3 glass-card rounded-2xl p-6">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
            Archive Captures ({filtered.length})
          </h3>

          <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
            {filtered.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`w-full text-left p-3 rounded-xl border transition ${
                  selectedItem?.id === item.id
                    ? 'bg-blue-600/15 border-blue-500/40 shadow-sm'
                    : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-xs font-bold text-white">{item.plate_number}</span>
                  <span className="text-[10px] text-emerald-400 font-bold">₹{item.total_fine}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className={`font-semibold ${VIOLATION_COLORS[item.violation_type]?.split(' ')[1] || 'text-slate-300'}`}>
                    {item.violation_type}
                  </span>
                  <span className="text-slate-400 text-[10px]">{item.timestamp?.split(' ')[1]}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Evidence;
