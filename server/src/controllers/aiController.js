import path from 'path';
import fs from 'fs';
import axios from 'axios';
import { dataStore } from '../services/dataStore.js';
import { ENV } from '../config/env.js';

let localSignalState = {
  state: 'GREEN',
  autoCycle: true,
  activeDirection: 'NORTH',
  remainingSeconds: 15,
  lanes: {
    NORTH: { vehicle_count: 4, green_seconds: 15 },
    EAST: { vehicle_count: 1, green_seconds: 5 },
    SOUTH: { vehicle_count: 3, green_seconds: 8 },
    WEST: { vehicle_count: 2, green_seconds: 6 },
  },
};

export const processVideo = async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No video file was uploaded.',
      });
    }

    const jobId = `JOB_${Date.now()}_${Math.round(Math.random() * 1e4)}`;
    const jobData = {
      job_id: jobId,
      status: 'PROCESSING',
      filename: req.file.filename,
      original_name: req.file.originalname,
      progress: 0,
      total_frames: 0,
      processed_frames: 0,
      violations_detected: 0,
      violations: [],
      persisted_violation_keys: [],
    };

    await dataStore.createJob(jobData);

    // Forward to Python AI microservice asynchronously
    try {
      axios.post(`${ENV.AI_SERVICE_URL}/process/video`, {
        job_id: jobId,
        file_path: req.file.path,
        speed_limit: parseFloat(req.body.speedLimit) || 50.0,
      }).catch((err) => {
        console.warn(`[AI Bridge] Python microservice connection deferred: ${err.message}`);
      });
    } catch (e) {
      // Async fire-and-forget
    }

    return res.status(202).json({
      success: true,
      message: 'Video upload accepted and queued for computer-vision inference.',
      jobId,
      filename: req.file.filename,
      videoUrl: `/uploads/${req.file.filename}`,
    });
  } catch (error) {
    next(error);
  }
};

export const processSampleVideo = async (req, res, next) => {
  try {
    const samplePath = path.join(ENV.UPLOAD_DIR, 'sample_traffic.mp4');
    if (!fs.existsSync(samplePath)) {
      return res.status(404).json({
        success: false,
        message: 'Sample traffic video not found in storage/uploads.',
      });
    }

    const jobId = `JOB_SAMPLE_${Date.now()}_${Math.round(Math.random() * 1e4)}`;
    const jobData = {
      job_id: jobId,
      status: 'PROCESSING',
      filename: 'sample_traffic.mp4',
      original_name: 'sample_traffic.mp4',
      progress: 0,
      total_frames: 0,
      processed_frames: 0,
      violations_detected: 0,
      violations: [],
      persisted_violation_keys: [],
    };

    await dataStore.createJob(jobData);

    // Forward to Python AI microservice
    try {
      axios.post(`${ENV.AI_SERVICE_URL}/process/video`, {
        job_id: jobId,
        file_path: samplePath,
        speed_limit: parseFloat(req.body.speedLimit) || 50.0,
      }).catch((err) => {
        console.warn(`[AI Bridge] Python microservice deferred: ${err.message}`);
      });
    } catch (e) {
      // Async
    }

    return res.status(202).json({
      success: true,
      message: 'Sample traffic surveillance queued for real-time inference.',
      jobId,
      filename: 'sample_traffic.mp4',
      videoUrl: '/uploads/sample_traffic.mp4',
    });
  } catch (error) {
    next(error);
  }
};

export const getJobStatus = async (req, res, next) => {
  try {
    const { jobId } = req.params;
    let job = await dataStore.getJob(jobId);

    // Always attempt syncing live status from Python AI service
    try {
      const aiRes = await axios.get(`${ENV.AI_SERVICE_URL}/jobs/${jobId}`, { timeout: 3000 });
      if (aiRes.data) {
        const aiData = aiRes.data;

        if (!job) {
          job = {
            job_id: jobId,
            status: aiData.status,
            progress: aiData.progress,
            total_frames: aiData.total_frames,
            processed_frames: aiData.processed_frames,
            violations_detected: aiData.violations_count,
            violations: aiData.violations || [],
            persisted_violation_keys: [],
          };
          await dataStore.createJob(job);
        } else {
          job.status = aiData.status;
          job.progress = aiData.progress;
          job.total_frames = aiData.total_frames;
          job.processed_frames = aiData.processed_frames;
          job.violations_detected = aiData.violations_count;
          job.violations = aiData.violations || [];
        }

        // Persist newly discovered violations into dataStore and compound secondary penalties
        const persistedKeys = job.persisted_violation_keys || [];
        if (Array.isArray(aiData.violations) && aiData.violations.length > 0) {
          for (const v of aiData.violations) {
            const vKey = `${v.tracking_id}_${v.violation_type}`;
            if (!persistedKeys.includes(vKey)) {
              // Lookup vehicle in VAHAN database (only if plate is readable)
              const isUnreadable = !v.plate_number || v.plate_number === 'UNREADABLE' || v.plate_number === 'UNKNOWN';
              const cleanPlate = isUnreadable ? 'UNREADABLE' : v.plate_number.toUpperCase();
              const vehicle = !isUnreadable ? await dataStore.getVehicleByPlate(cleanPlate) : null;

              let secondary_fine = 0;
              const secondaryNotes = [];
              if (vehicle) {
                if (vehicle.insurance_status === 'EXPIRED') {
                  secondary_fine += 2000;
                  secondaryNotes.push('Expired Insurance (+₹2000)');
                }
                if (vehicle.puc_status === 'EXPIRED') {
                  secondary_fine += 1000;
                  secondaryNotes.push('Expired PUC (+₹1000)');
                }
              }

              const primaryFine = v.primary_fine || 1000;
              const totalFine = primaryFine + secondary_fine;
              let detailsText = v.details || v.violation_type;
              if (secondaryNotes.length > 0) {
                detailsText += ` [Secondary Penalty: ${secondaryNotes.join(', ')}]`;
              }
              if (isUnreadable) {
                detailsText += ` [ANPR Note: License plate illegible - flagged for manual officer photographic review]`;
              }

              const snapshotPath = v.evidence_path
                ? (v.evidence_path.startsWith('/') ? v.evidence_path : `/evidence/${path.basename(v.evidence_path)}`)
                : '';

              const ownerName = isUnreadable
                ? 'Unidentified Vehicle (Manual Audit Required)'
                : (vehicle?.owner_name || `Citizen Owner (${cleanPlate})`);

              await dataStore.createViolation({
                tracking_id: v.tracking_id,
                plate_number: cleanPlate,
                owner_name: ownerName,
                violation_type: v.violation_type,
                speed_recorded: v.speed_recorded || null,
                primary_fine: primaryFine,
                secondary_fine,
                total_fine: totalFine,
                snapshot_path: snapshotPath,
                challan_status: 'ISSUED',
                review_status: 'PENDING',
                sms_status: isUnreadable ? 'FAILED' : 'SIMULATED',
                details: detailsText,
                source_video: job.filename || 'sample_traffic.mp4',
                plate_box: v.plate_box || null,
                plate_confidence: v.plate_confidence || 0.0,
                plate_status: v.plate_status || (isUnreadable ? 'DETECTED_UNREADABLE' : 'DETECTED_READ'),
                raw_ocr_text: v.raw_ocr_text || '',
                verification_status: (!isUnreadable && v.verification_status === 'VERIFIED_ANPR' && (v.plate_confidence || 0) >= 0.60) ? 'VERIFIED_ANPR' : 'UNVERIFIED_MANUAL_REVIEW',
              });

              persistedKeys.push(vKey);
            }
          }
          job.persisted_violation_keys = persistedKeys;
        }

        await dataStore.updateJob(jobId, job);
      }
    } catch (e) {
      // AI Service offline or timeout - fallback to existing job record
    }

    if (!job) {
      return res.status(404).json({
        success: false,
        message: `Processing Job #${jobId} not found.`,
      });
    }

    return res.json({
      success: true,
      data: job,
    });
  } catch (error) {
    next(error);
  }
};

export const getSignalState = async (req, res, next) => {
  try {
    try {
      const aiRes = await axios.get(`${ENV.AI_SERVICE_URL}/signal/state`, { timeout: 1500 });
      if (aiRes.data) {
        return res.json({ success: true, data: aiRes.data });
      }
    } catch (e) {}

    return res.json({
      success: true,
      data: localSignalState,
    });
  } catch (error) {
    next(error);
  }
};

export const overrideSignal = async (req, res, next) => {
  try {
    const { state, autoCycle, direction } = req.body;
    if (state) localSignalState.state = state;
    if (autoCycle !== undefined) localSignalState.autoCycle = autoCycle;
    if (direction) localSignalState.activeDirection = direction;

    try {
      await axios.post(`${ENV.AI_SERVICE_URL}/signal/override`, req.body, { timeout: 1500 });
    } catch (e) {}

    return res.json({
      success: true,
      message: `Junction traffic signal overridden to ${state || localSignalState.state}.`,
      data: localSignalState,
    });
  } catch (error) {
    next(error);
  }
};
