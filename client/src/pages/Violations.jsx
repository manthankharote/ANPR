import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  CreditCard,
  Send,
  Eye,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { violationService } from '../services/violationService';
import Badge from '../components/common/Badge';
import { VIOLATION_COLORS, VIOLATION_TYPES } from '../utils/constants';

const SAMPLE_VIOLATIONS = [
  {
    id: 1261,
    timestamp: '2026-10-26 18:42:10',
    plate_number: 'KA03MJ4321',
    owner_name: 'Suresh Reddy',
    violation_type: 'No Helmet',
    speed_recorded: null,
    primary_fine: 1000,
    secondary_fine: 3000,
    total_fine: 4000,
    challan_status: 'ISSUED',
    review_status: 'PENDING',
    sms_status: 'SIMULATED',
    details: 'Rider operating two-wheeler without protective helmet [Secondary Penalty: Expired Insurance (+₹2000), Expired PUC (+₹1000)]',
  },
  {
    id: 1260,
    timestamp: '2026-10-26 18:35:45',
    plate_number: 'MH14GH4321',
    owner_name: 'Nikhil Kulkarni',
    violation_type: 'No Helmet',
    speed_recorded: null,
    primary_fine: 1000,
    secondary_fine: 0,
    total_fine: 1000,
    challan_status: 'PAID',
    review_status: 'CONFIRMED',
    sms_status: 'SIMULATED',
    details: 'Rider operating two-wheeler without protective helmet',
  },
  {
    id: 1259,
    timestamp: '2026-10-26 18:22:18',
    plate_number: 'DL01AB5555',
    owner_name: 'Amitabh Verma',
    violation_type: 'Red Light Jump',
    speed_recorded: null,
    primary_fine: 1000,
    secondary_fine: 1000,
    total_fine: 2000,
    challan_status: 'ISSUED',
    review_status: 'CONFIRMED',
    sms_status: 'SIMULATED',
    details: 'Jumped red light signal at Stop Line (Y=480) [Secondary Penalty: Expired PUC (+₹1000)]',
  },
  {
    id: 1258,
    timestamp: '2026-10-26 18:10:04',
    plate_number: 'MH12XY9876',
    owner_name: 'Pooja Deshmukh',
    violation_type: 'Over-Speeding',
    speed_recorded: 72.4,
    primary_fine: 2000,
    secondary_fine: 2000,
    total_fine: 4000,
    challan_status: 'ISSUED',
    review_status: 'PENDING',
    sms_status: 'SIMULATED',
    details: 'Clocked at 72.4 km/h (Limit: 50.0 km/h) [Secondary Penalty: Expired Insurance (+₹2000)]',
  },
  {
    id: 1257,
    timestamp: '2026-10-26 17:55:12',
    plate_number: 'MH20AB1234',
    owner_name: 'Rajesh Sharma',
    violation_type: 'Red Light Jump',
    speed_recorded: null,
    primary_fine: 1000,
    secondary_fine: 0,
    total_fine: 1000,
    challan_status: 'ISSUED',
    review_status: 'CONFIRMED',
    sms_status: 'SIMULATED',
    details: 'Crossed Stop Line during RED Signal phase',
  },
  {
    id: 1256,
    timestamp: '2026-10-26 17:40:30',
    plate_number: 'GJ01BC9999',
    owner_name: 'Harish Patel',
    violation_type: 'Wrong-Lane / Wrong-Way Driving',
    speed_recorded: null,
    primary_fine: 1500,
    secondary_fine: 0,
    total_fine: 1500,
    challan_status: 'ISSUED',
    review_status: 'PENDING',
    sms_status: 'SIMULATED',
    details: 'Commercial vehicle moving against designated roadway flow vector',
  },
];

const Violations = () => {
  const [violations, setViolations] = useState(SAMPLE_VIOLATIONS);
  const [searchPlate, setSearchPlate] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [actionNotice, setActionNotice] = useState('');

  useEffect(() => {
    const fetchViolations = async () => {
      try {
        const res = await violationService.getViolations({ limit: 100 });
        if (res.data?.length) {
          setViolations(res.data);
        }
      } catch (e) {
        // Fallback to sample data
      }
    };
    fetchViolations();
  }, []);

  const handleReviewAction = async (id, status) => {
    try {
      await violationService.reviewViolation(id, { review_status: status });
    } catch (e) {
      // Local state update
    }

    setViolations(
      violations.map((v) => (v.id === id ? { ...v, review_status: status } : v))
    );
    if (selectedViolation?.id === id) {
      setSelectedViolation({ ...selectedViolation, review_status: status });
    }
    setActionNotice(`Violation #${id} marked as ${status}`);
    setTimeout(() => setActionNotice(''), 3000);
  };

  const handleMarkPaid = async (id) => {
    try {
      await violationService.reviewViolation(id, { challan_status: 'PAID' });
    } catch (e) {
      // Local state update
    }

    setViolations(
      violations.map((v) => (v.id === id ? { ...v, challan_status: 'PAID' } : v))
    );
    if (selectedViolation?.id === id) {
      setSelectedViolation({ ...selectedViolation, challan_status: 'PAID' });
    }
    setActionNotice(`Challan #${id} settled and marked as PAID.`);
    setTimeout(() => setActionNotice(''), 3000);
  };

  const filteredViolations = violations.filter((v) => {
    const cleanSearch = searchPlate.replace(/\s+/g, '').toUpperCase();
    const matchesPlate = !cleanSearch || v.plate_number.includes(cleanSearch);
    const matchesType = filterType === 'ALL' || v.violation_type === filterType;
    const matchesStatus =
      filterStatus === 'ALL' || v.review_status === filterStatus || v.challan_status === filterStatus;
    return matchesPlate && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Traffic Violation & e-Challan Records</h1>
          <p className="text-xs text-slate-400 mt-1">
            Statutory violation audit trail with officer confirmation, dispute rejection & secondary fine breakdowns.
          </p>
        </div>

        {actionNotice && (
          <div className="px-4 py-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-bold animate-pulse">
            ✓ {actionNotice}
          </div>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-card rounded-2xl p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchPlate}
            onChange={(e) => setSearchPlate(e.target.value)}
            placeholder="Search by license plate..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-xs text-white placeholder-slate-500 uppercase font-mono"
          />
        </div>

        {/* Category Filter */}
        <div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl glass-input text-xs text-white"
          >
            <option value="ALL">All Violation Types</option>
            {VIOLATION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full py-2.5 px-3 rounded-xl glass-input text-xs text-white"
          >
            <option value="ALL">All Review & Payment Statuses</option>
            <option value="PENDING">Pending Review</option>
            <option value="CONFIRMED">Officer Confirmed</option>
            <option value="REJECTED">Disputed / Rejected</option>
            <option value="PAID">Settled / Paid</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold bg-slate-900/50">
                <th className="py-3.5 px-4">Challan Reference</th>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Plate Number</th>
                <th className="py-3.5 px-4">Registered Owner</th>
                <th className="py-3.5 px-4">Offense</th>
                <th className="py-3.5 px-4">Primary Fine</th>
                <th className="py-3.5 px-4">Secondary (Doc)</th>
                <th className="py-3.5 px-4">Total Amount</th>
                <th className="py-3.5 px-4">Review Status</th>
                <th className="py-3.5 px-4">Challan State</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredViolations.map((v) => (
                <tr key={v.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-slate-400">#E-CH-2026-{v.id}</td>
                  <td className="py-3.5 px-4 text-slate-400">{v.timestamp}</td>
                  <td className="py-3.5 px-4">
                    <span className={`font-mono font-bold px-2 py-0.5 rounded border text-xs ${
                      v.plate_number === 'UNREADABLE'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-white text-slate-900 border-black'
                    }`}>
                      {v.plate_number}
                    </span>
                    {v.verification_status && (
                      <span className={`block text-[9px] font-mono mt-0.5 ${v.verification_status === 'VERIFIED_ANPR' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {v.verification_status === 'VERIFIED_ANPR' ? '✓ ANPR' : '⚠ AUDIT'}
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-white">{v.owner_name}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                        VIOLATION_COLORS[v.violation_type] || 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {v.violation_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">₹{v.primary_fine}</td>
                  <td className="py-3.5 px-4">
                    {v.secondary_fine > 0 ? (
                      <span className="text-rose-400 font-bold">+₹{v.secondary_fine}</span>
                    ) : (
                      <span className="text-slate-500">₹0</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-black text-emerald-400">₹{v.total_fine}</td>
                  <td className="py-3.5 px-4">
                    <Badge
                      variant={
                        v.review_status === 'CONFIRMED'
                          ? 'success'
                          : v.review_status === 'REJECTED'
                          ? 'danger'
                          : 'warning'
                      }
                    >
                      {v.review_status || 'PENDING'}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={v.challan_status === 'PAID' ? 'success' : 'default'}>
                      {v.challan_status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => setSelectedViolation(v)}
                      className="p-1.5 rounded-lg bg-blue-600/15 text-blue-400 hover:bg-blue-600/25 border border-blue-500/30 transition"
                      title="Inspect & Review"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review & Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card w-full max-w-2xl rounded-2xl p-6 border border-slate-700 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-lg font-black text-white">
                  Challan Audit Inspector #E-CH-2026-{selectedViolation.id}
                </h2>
                <p className="text-xs text-slate-400">{selectedViolation.timestamp}</p>
              </div>
              <button
                onClick={() => setSelectedViolation(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[11px] mb-1">Target Vehicle Plate</span>
                <span className="font-mono text-base font-bold bg-white text-slate-900 px-2 py-0.5 rounded border border-black inline-block">
                  {selectedViolation.plate_number}
                </span>
                <p className="text-white font-bold mt-2">{selectedViolation.owner_name}</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 block text-[11px] mb-1">Statutory Fine Breakdown</span>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Primary Fine:</span>
                    <span className="text-white font-bold">₹{selectedViolation.primary_fine}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Expired Doc Surcharge:</span>
                    <span className="text-rose-400 font-bold">+₹{selectedViolation.secondary_fine}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-slate-800 text-sm">
                    <span className="text-slate-200 font-bold">Total Assessed:</span>
                    <span className="text-emerald-400 font-black">₹{selectedViolation.total_fine}</span>
                  </div>
                </div>
              </div>
            </div>

            {selectedViolation.details && (
              <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 text-xs">
                <span className="text-slate-400 font-bold block mb-1">Sensor & Algorithmic Telemetry:</span>
                <p className="text-slate-300 font-mono text-[11px]">{selectedViolation.details}</p>
              </div>
            )}

            {/* Officer Human-in-the-Loop Actions */}
            <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleReviewAction(selectedViolation.id, 'CONFIRMED')}
                  className="py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow-md shadow-emerald-600/20"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Violation</span>
                </button>
                <button
                  onClick={() => handleReviewAction(selectedViolation.id, 'REJECTED')}
                  className="py-2 px-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow-md shadow-rose-600/20"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject / Dispute</span>
                </button>
              </div>

              <div className="flex items-center space-x-2">
                {selectedViolation.challan_status !== 'PAID' && (
                  <button
                    onClick={() => handleMarkPaid(selectedViolation.id)}
                    className="py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center space-x-1.5"
                  >
                    <CreditCard className="w-4 h-4" />
                    <span>Mark as PAID</span>
                  </button>
                )}
                <button
                  onClick={() => setSelectedViolation(null)}
                  className="py-2 px-3 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-bold"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Violations;
