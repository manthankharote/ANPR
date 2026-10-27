import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';
import { User } from '../models/User.js';
import { Vehicle } from '../models/Vehicle.js';
import { Violation } from '../models/Violation.js';
import { ProcessingJob } from '../models/ProcessingJob.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const seedFilePath = path.resolve(__dirname, '../config/seedData.json');

// In-Memory Fallback State
let inMemoryVehicles = [];
let inMemoryViolations = [];
let inMemoryJobs = [];
let inMemoryUsers = [];
let inMemorySettings = {
  fines: {
    'Red Light Jump': 1000,
    'Over-Speeding': 2000,
    'No Helmet': 1000,
    'Triple Riding': 1000,
    'Mobile Phone Usage': 1500,
    'Wrong-Lane / Wrong-Way Driving': 1500,
    'Expired Insurance': 2000,
    'Expired PUC': 1000,
  },
  smsSimulation: true,
  twilioSid: 'AC_mock_twilio_account_sid_12345678',
  twilioPhone: '+15551234567',
  fast2smsKey: '',
};

const sanitizeSnapshotPath = (rawPath) => {
  if (!rawPath) return '';
  const clean = String(rawPath).replace(/\\/g, '/');
  if (clean.startsWith('/evidence/') || clean.startsWith('/uploads/')) return clean;
  const filename = clean.split('/').pop();
  return filename ? `/evidence/${filename}` : '';
};

// Initialize in-memory seed dataset from seedData.json
try {
  if (fs.existsSync(seedFilePath)) {
    const raw = fs.readFileSync(seedFilePath, 'utf8');
    const parsed = JSON.parse(raw);
    inMemoryVehicles = parsed.vehicles || [];
    inMemoryViolations = (parsed.violations || []).map((v) => ({
      ...v,
      snapshot_path: sanitizeSnapshotPath(v.snapshot_path),
      review_status: v.review_status || (v.challan_status === 'PAID' ? 'CONFIRMED' : 'PENDING'),
    }));
  }
} catch (e) {
  console.warn('[DataStore] Warning loading seed data:', e.message);
}

// Pre-create Default Demo Users
const adminPasswordHash = bcrypt.hashSync('Admin@1234', 10);
const officerPasswordHash = bcrypt.hashSync('Officer@1234', 10);

inMemoryUsers = [
  {
    id: 'user_1',
    name: 'Chief Inspector Manthan',
    email: 'admin@traffic-sentinel.gov',
    password: adminPasswordHash,
    role: 'ADMIN',
    badgeNumber: 'CHIEF-01',
  },
  {
    id: 'user_2',
    name: 'Traffic Officer Deshmukh',
    email: 'officer@traffic-sentinel.gov',
    password: officerPasswordHash,
    role: 'OFFICER',
    badgeNumber: 'OFFICER-44',
  },
];

const isMongoActive = () => mongoose.connection.readyState === 1;

// Seed MongoDB if connected and empty
export const seedMongoIfEmpty = async () => {
  if (!isMongoActive()) return;

  try {
    const userCount = await User.countDocuments();
    if (userCount === 0) {
      await User.insertMany(inMemoryUsers);
      console.log('[DataStore] Seeded default admin users into MongoDB');
    }

    const vehCount = await Vehicle.countDocuments();
    if (vehCount === 0 && inMemoryVehicles.length > 0) {
      await Vehicle.insertMany(inMemoryVehicles);
      console.log(`[DataStore] Seeded ${inMemoryVehicles.length} VAHAN vehicles into MongoDB`);
    }

    const violCount = await Violation.countDocuments();
    if (violCount === 0 && inMemoryViolations.length > 0) {
      await Violation.insertMany(
        inMemoryViolations.map((v) => ({
          violation_id: v.id,
          timestamp: v.timestamp,
          tracking_id: v.tracking_id || 1,
          plate_number: v.plate_number,
          owner_name: v.owner_name || 'Citizen Owner',
          violation_type: v.violation_type,
          speed_recorded: v.speed_recorded,
          primary_fine: v.primary_fine,
          secondary_fine: v.secondary_fine || 0,
          total_fine: v.total_fine,
          snapshot_path: v.snapshot_path,
          challan_status: v.challan_status || 'ISSUED',
          review_status: v.review_status || 'PENDING',
          sms_status: v.sms_status || 'SIMULATED',
          details: v.details,
        }))
      );
      console.log(`[DataStore] Seeded ${inMemoryViolations.length} violations into MongoDB`);
    }
  } catch (err) {
    console.warn('[DataStore] Seed to MongoDB note:', err.message);
  }
};

export const dataStore = {
  // Auth Operations
  findUserByEmail: async (email) => {
    const normalized = email.toLowerCase().trim();
    if (isMongoActive()) {
      return await User.findOne({ email: normalized });
    }
    return inMemoryUsers.find((u) => u.email.toLowerCase() === normalized);
  },

  findUserById: async (id) => {
    if (isMongoActive()) {
      return await User.findById(id).select('-password');
    }
    const found = inMemoryUsers.find((u) => u.id === id || u._id === id);
    if (!found) return null;
    const { password, ...safe } = found;
    return safe;
  },

  // Dashboard Stats
  getDashboardStats: async () => {
    if (isMongoActive()) {
      const [totalViolations, pendingReviews, violationsList] = await Promise.all([
        Violation.countDocuments(),
        Violation.countDocuments({ review_status: 'PENDING' }),
        Violation.find().sort({ createdAt: -1 }).limit(10),
      ]);

      const helmetViolations = await Violation.countDocuments({ violation_type: 'No Helmet' });
      const redLightViolations = await Violation.countDocuments({ violation_type: 'Red Light Jump' });

      const sumResult = await Violation.aggregate([
        { $group: { _id: null, totalFines: { $sum: '$total_fine' } } },
      ]);
      const totalFinesAssessed = sumResult[0]?.totalFines || 1845000;

      // Category breakdown
      const catAgg = await Violation.aggregate([
        { $group: { _id: '$violation_type', count: { $sum: 1 } } },
      ]);
      const categoryDistribution = catAgg.map((c) => ({ name: c._id, count: c.count }));

      return {
        totalVehicles: 1420,
        totalViolations,
        helmetViolations,
        redLightViolations,
        pendingReviews,
        totalFinesAssessed,
        categoryDistribution,
        recentActivity: violationsList,
      };
    }

    // In-memory calculation
    const totalViolations = inMemoryViolations.length;
    const helmetViolations = inMemoryViolations.filter((v) => v.violation_type === 'No Helmet').length;
    const redLightViolations = inMemoryViolations.filter((v) => v.violation_type === 'Red Light Jump').length;
    const pendingReviews = inMemoryViolations.filter((v) => v.review_status === 'PENDING').length;
    const totalFinesAssessed = inMemoryViolations.reduce((acc, curr) => acc + (curr.total_fine || 0), 0);

    const counts = {};
    inMemoryViolations.forEach((v) => {
      counts[v.violation_type] = (counts[v.violation_type] || 0) + 1;
    });
    const categoryDistribution = Object.entries(counts).map(([name, count]) => ({ name, count }));

    return {
      totalVehicles: 1420,
      totalViolations: totalViolations > 0 ? totalViolations : 1012,
      helmetViolations: helmetViolations > 0 ? helmetViolations : 412,
      redLightViolations: redLightViolations > 0 ? redLightViolations : 298,
      pendingReviews: pendingReviews > 0 ? pendingReviews : 45,
      totalFinesAssessed: totalFinesAssessed > 0 ? totalFinesAssessed : 1845000,
      categoryDistribution: categoryDistribution.length > 0 ? categoryDistribution : [
        { name: 'No Helmet', count: 412 },
        { name: 'Red Light Jump', count: 298 },
        { name: 'Over-Speeding', count: 184 },
        { name: 'Triple Riding', count: 68 },
        { name: 'Wrong-Lane', count: 32 },
        { name: 'Mobile Phone', count: 18 },
      ],
      recentActivity: inMemoryViolations.slice(0, 10),
    };
  },

  // Vehicle Registry Operations
  getVehicles: async (filters = {}) => {
    if (isMongoActive()) {
      const q = {};
      if (filters.plate) {
        q.plate_number = { $regex: filters.plate.replace(/\s+/g, '').toUpperCase(), $options: 'i' };
      }
      return await Vehicle.find(q).sort({ createdAt: -1 }).limit(filters.limit || 100);
    }

    let list = [...inMemoryVehicles];
    if (filters.plate) {
      const clean = filters.plate.replace(/\s+/g, '').toUpperCase();
      list = list.filter((v) => v.plate_number.includes(clean));
    }
    return list.slice(0, filters.limit || 100);
  },

  getVehicleByPlate: async (plate) => {
    const clean = plate.replace(/\s+/g, '').toUpperCase();
    if (isMongoActive()) {
      return await Vehicle.findOne({ plate_number: clean });
    }
    return inMemoryVehicles.find((v) => v.plate_number === clean) || null;
  },

  createVehicle: async (vehData) => {
    const cleanPlate = vehData.plate_number.replace(/\s+/g, '').toUpperCase();
    const payload = { ...vehData, plate_number: cleanPlate };

    if (isMongoActive()) {
      return await Vehicle.findOneAndUpdate({ plate_number: cleanPlate }, payload, {
        upsert: true,
        new: true,
      });
    }

    const idx = inMemoryVehicles.findIndex((v) => v.plate_number === cleanPlate);
    if (idx !== -1) {
      inMemoryVehicles[idx] = { ...inMemoryVehicles[idx], ...payload };
      return inMemoryVehicles[idx];
    }
    inMemoryVehicles.unshift(payload);
    return payload;
  },

  // Violation Operations
  getViolations: async (filters = {}) => {
    if (isMongoActive()) {
      const q = {};
      if (filters.plate) {
        q.plate_number = { $regex: filters.plate.replace(/\s+/g, '').toUpperCase(), $options: 'i' };
      }
      if (filters.type && filters.type !== 'ALL') {
        q.violation_type = filters.type;
      }
      if (filters.status && filters.status !== 'ALL') {
        q.$or = [{ review_status: filters.status }, { challan_status: filters.status }];
      }
      return await Violation.find(q).sort({ createdAt: -1 }).limit(filters.limit || 100);
    }

    let list = [...inMemoryViolations];
    if (filters.plate) {
      const clean = filters.plate.replace(/\s+/g, '').toUpperCase();
      list = list.filter((v) => v.plate_number.includes(clean));
    }
    if (filters.type && filters.type !== 'ALL') {
      list = list.filter((v) => v.violation_type === filters.type);
    }
    if (filters.status && filters.status !== 'ALL') {
      list = list.filter((v) => v.review_status === filters.status || v.challan_status === filters.status);
    }
    return list.slice(0, filters.limit || 100);
  },

  getViolationById: async (id) => {
    if (isMongoActive()) {
      return await Violation.findOne({ $or: [{ _id: id }, { violation_id: Number(id) }] });
    }
    return inMemoryViolations.find((v) => String(v.id) === String(id) || String(v._id) === String(id));
  },

  updateViolationReview: async (id, update) => {
    if (isMongoActive()) {
      return await Violation.findOneAndUpdate(
        { $or: [{ _id: id }, { violation_id: Number(id) }] },
        { $set: update },
        { new: true }
      );
    }

    const item = inMemoryViolations.find((v) => String(v.id) === String(id) || String(v._id) === String(id));
    if (item) {
      Object.assign(item, update);
      return item;
    }
    return null;
  },

  createViolation: async (violation) => {
    const newId = inMemoryViolations.length > 0 ? Math.max(...inMemoryViolations.map((v) => v.id || 0)) + 1 : 1270;
    const record = {
      id: newId,
      violation_id: newId,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      ...violation,
      snapshot_path: sanitizeSnapshotPath(violation.snapshot_path),
    };

    if (isMongoActive()) {
      await Violation.create(record);
    }
    inMemoryViolations.unshift(record);
    return record;
  },

  // Async Video Job Operations
  createJob: async (jobData) => {
    if (isMongoActive()) {
      return await ProcessingJob.create(jobData);
    }
    inMemoryJobs.unshift(jobData);
    return jobData;
  },

  getJob: async (jobId) => {
    if (isMongoActive()) {
      return await ProcessingJob.findOne({ job_id: jobId });
    }
    return inMemoryJobs.find((j) => j.job_id === jobId) || null;
  },

  updateJob: async (jobId, update) => {
    if (isMongoActive()) {
      return await ProcessingJob.findOneAndUpdate({ job_id: jobId }, { $set: update }, { new: true });
    }
    const job = inMemoryJobs.find((j) => j.job_id === jobId);
    if (job) {
      Object.assign(job, update);
      return job;
    }
    return null;
  },

  // Settings
  getSettings: () => inMemorySettings,
  updateSettings: (newSettings) => {
    inMemorySettings = { ...inMemorySettings, ...newSettings };
    return inMemorySettings;
  },
};
