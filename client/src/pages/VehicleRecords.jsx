import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Car,
  ShieldCheck,
  ShieldAlert,
  Calendar,
  Phone,
  MapPin,
  CheckCircle,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { violationService } from '../services/violationService';
import Badge from '../components/common/Badge';

const SAMPLE_VEHICLES = [
  {
    plate_number: 'MH20AB1234',
    owner_name: 'Rajesh Sharma',
    vehicle_model: 'Hyundai Creta SX',
    vehicle_type: 'Car',
    insurance_expiry: '2027-05-20',
    insurance_status: 'VALID',
    puc_expiry: '2027-05-20',
    puc_status: 'VALID',
    registered_rto: 'MH-20 Sambhajinagar (Aurangabad)',
    mobile_number: '+919822012345',
  },
  {
    plate_number: 'MH12XY9876',
    owner_name: 'Pooja Deshmukh',
    vehicle_model: 'Honda Activa 6G',
    vehicle_type: 'Motorcycle',
    insurance_expiry: '2026-06-15',
    insurance_status: 'EXPIRED',
    puc_expiry: '2027-08-10',
    puc_status: 'VALID',
    registered_rto: 'MH-12 Pune Central',
    mobile_number: '+919890123456',
  },
  {
    plate_number: 'DL01AB5555',
    owner_name: 'Amitabh Verma',
    vehicle_model: 'Maruti Suzuki Swift Dzire',
    vehicle_type: 'Car',
    insurance_expiry: '2027-04-12',
    insurance_status: 'VALID',
    puc_expiry: '2026-09-01',
    puc_status: 'EXPIRED',
    registered_rto: 'DL-01 Delhi North',
    mobile_number: '+919811223344',
  },
  {
    plate_number: 'KA03MJ4321',
    owner_name: 'Suresh Reddy',
    vehicle_model: 'Royal Enfield Classic 350',
    vehicle_type: 'Motorcycle',
    insurance_expiry: '2026-08-20',
    insurance_status: 'EXPIRED',
    puc_expiry: '2026-07-15',
    puc_status: 'EXPIRED',
    registered_rto: 'KA-03 Bengaluru East (Indiranagar)',
    mobile_number: '+919945678901',
  },
  {
    plate_number: 'GJ01BC9999',
    owner_name: 'Harish Patel',
    vehicle_model: 'Tata Prima 4028.S',
    vehicle_type: 'Truck',
    insurance_expiry: '2027-09-11',
    insurance_status: 'VALID',
    puc_expiry: '2027-03-30',
    puc_status: 'VALID',
    registered_rto: 'GJ-01 Ahmedabad West',
    mobile_number: '+919825099887',
  },
];

const VehicleRecords = () => {
  const [vehicles, setVehicles] = useState(SAMPLE_VEHICLES);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState(SAMPLE_VEHICLES[0]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newVehicle, setNewVehicle] = useState({
    plate_number: '',
    owner_name: '',
    vehicle_model: '',
    vehicle_type: 'Car',
    insurance_status: 'VALID',
    insurance_expiry: '2027-10-26',
    puc_status: 'VALID',
    puc_expiry: '2027-10-26',
    registered_rto: 'MH-14 Pimpri-Chinchwad',
    mobile_number: '+919800000000',
  });

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const res = await violationService.getVehicles();
        if (res.data?.length) {
          setVehicles(res.data);
          setSelectedVehicle(res.data[0]);
        }
      } catch (err) {
        // Fallback to sample vehicles
      }
    };
    fetchVehicles();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    const clean = searchQuery.replace(/\s+/g, '').toUpperCase();
    const found = vehicles.find((v) => v.plate_number.includes(clean));
    if (found) {
      setSelectedVehicle(found);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    const cleanPlate = newVehicle.plate_number.replace(/\s+/g, '').toUpperCase();
    const payload = { ...newVehicle, plate_number: cleanPlate };

    try {
      await violationService.createVehicle(payload);
    } catch (e) {
      // Local addition
    }

    setVehicles([payload, ...vehicles]);
    setSelectedVehicle(payload);
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">VAHAN Vehicle Registry</h1>
          <p className="text-xs text-slate-400 mt-1">
            National transport vehicle database with automated Insurance & PUC secondary penalty linkage.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-blue-600/25 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Vehicle</span>
        </button>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="glass-card rounded-2xl p-4 flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Registration Plate (e.g., MH20AB1234, DL01AB5555, KA03MJ4321)..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-xs text-white placeholder-slate-500 font-mono uppercase"
          />
        </div>
        <button
          type="submit"
          className="py-2.5 px-5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition"
        >
          Lookup VAHAN
        </button>
      </form>

      {/* Selected Vehicle Profile Card & Document Verification */}
      {selectedVehicle && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info Card (2 cols) */}
          <div className="lg:col-span-2 glass-card rounded-2xl p-6 border-l-4 border-l-blue-500">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <span className="font-mono text-base font-black bg-white text-slate-900 px-3 py-1 rounded-md border border-black shadow-sm">
                {selectedVehicle.plate_number}
              </span>
              <span className="text-xs font-bold text-blue-400 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
                {selectedVehicle.vehicle_type}
              </span>
            </div>

            <h2 className="text-xl font-black text-white">{selectedVehicle.owner_name}</h2>
            <p className="text-xs text-slate-400 mt-0.5">Model: {selectedVehicle.vehicle_model}</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-800 text-xs">
              <div className="flex items-start space-x-3">
                <MapPin className="w-4 h-4 text-slate-400 mt-0.5" />
                <div>
                  <span className="text-slate-400 block text-[11px]">Registered RTO:</span>
                  <span className="font-semibold text-white">{selectedVehicle.registered_rto}</span>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <Phone className="w-4 h-4 text-slate-400 mt-0.5" />
                <div>
                  <span className="text-slate-400 block text-[11px]">Registered Mobile:</span>
                  <span className="font-semibold text-white">{selectedVehicle.mobile_number}</span>
                </div>
              </div>
            </div>

            {/* Insurance & PUC Inspection Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
              {/* Insurance */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300">Motor Insurance Policy</span>
                  <Badge variant={selectedVehicle.insurance_status === 'VALID' ? 'success' : 'danger'}>
                    {selectedVehicle.insurance_status}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400">
                  Expiry Date: <span className="font-mono font-bold text-slate-200">{selectedVehicle.insurance_expiry}</span>
                </p>
                {selectedVehicle.insurance_status === 'EXPIRED' && (
                  <p className="text-[11px] font-bold text-rose-400 mt-2">
                    ⚠️ Triggers statutory secondary fine (+₹2,000)
                  </p>
                )}
              </div>

              {/* PUC */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300">PUC Emission Certificate</span>
                  <Badge variant={selectedVehicle.puc_status === 'VALID' ? 'success' : 'danger'}>
                    {selectedVehicle.puc_status}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400">
                  Expiry Date: <span className="font-mono font-bold text-slate-200">{selectedVehicle.puc_expiry}</span>
                </p>
                {selectedVehicle.puc_status === 'EXPIRED' && (
                  <p className="text-[11px] font-bold text-rose-400 mt-2">
                    ⚠️ Triggers statutory secondary fine (+₹1,000)
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Quick Select Registered Vehicles (1 col) */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Browse Vehicles
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {vehicles.map((v) => (
                <button
                  key={v.plate_number}
                  onClick={() => setSelectedVehicle(v)}
                  className={`w-full text-left p-3 rounded-xl border transition ${
                    selectedVehicle.plate_number === v.plate_number
                      ? 'bg-blue-600/15 border-blue-500/40'
                      : 'bg-slate-900/50 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-xs font-bold text-white">{v.plate_number}</span>
                    <span className="text-[10px] text-slate-400">{v.vehicle_type}</span>
                  </div>
                  <p className="text-xs text-slate-300 truncate">{v.owner_name}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add Vehicle Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card w-full max-w-lg rounded-2xl p-6 border border-slate-700 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-4">Register New VAHAN Vehicle</h2>
            <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-400 mb-1">License Plate</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., MH14GH4321"
                    value={newVehicle.plate_number}
                    onChange={(e) => setNewVehicle({ ...newVehicle, plate_number: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input uppercase font-mono"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-400 mb-1">Vehicle Type</label>
                  <select
                    value={newVehicle.vehicle_type}
                    onChange={(e) => setNewVehicle({ ...newVehicle, vehicle_type: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input text-white"
                  >
                    <option value="Car">Car</option>
                    <option value="Motorcycle">Motorcycle</option>
                    <option value="Truck">Truck</option>
                    <option value="Bus">Bus</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-400 mb-1">Owner Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Rohit Patil"
                  value={newVehicle.owner_name}
                  onChange={(e) => setNewVehicle({ ...newVehicle, owner_name: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-400 mb-1">Vehicle Model</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., Tata Harrier"
                    value={newVehicle.vehicle_model}
                    onChange={(e) => setNewVehicle({ ...newVehicle, vehicle_model: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input text-white"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-400 mb-1">Mobile Contact</label>
                  <input
                    type="text"
                    required
                    value={newVehicle.mobile_number}
                    onChange={(e) => setNewVehicle({ ...newVehicle, mobile_number: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-400 mb-1">Insurance Status</label>
                  <select
                    value={newVehicle.insurance_status}
                    onChange={(e) => setNewVehicle({ ...newVehicle, insurance_status: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input text-white"
                  >
                    <option value="VALID">VALID</option>
                    <option value="EXPIRED">EXPIRED</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-slate-400 mb-1">PUC Status</label>
                  <select
                    value={newVehicle.puc_status}
                    onChange={(e) => setNewVehicle({ ...newVehicle, puc_status: e.target.value })}
                    className="w-full p-2.5 rounded-xl glass-input text-white"
                  >
                    <option value="VALID">VALID</option>
                    <option value="EXPIRED">EXPIRED</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="py-2 px-4 rounded-xl text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="py-2 px-5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold"
                >
                  Save to Registry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleRecords;
