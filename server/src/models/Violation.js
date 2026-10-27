import mongoose from 'mongoose';

const violationSchema = new mongoose.Schema(
  {
    violation_id: {
      type: Number,
      index: true,
    },
    timestamp: {
      type: String,
      required: true,
      index: true,
    },
    tracking_id: {
      type: Number,
      required: true,
    },
    plate_number: {
      type: String,
      required: true,
      uppercase: true,
      index: true,
    },
    owner_name: {
      type: String,
      default: 'Citizen Owner',
    },
    violation_type: {
      type: String,
      required: true,
      enum: [
        'Red Light Jump',
        'Over-Speeding',
        'No Helmet',
        'Triple Riding',
        'Wrong-Lane / Wrong-Way Driving',
        'Mobile Phone Usage',
        'Expired Insurance',
        'Expired PUC',
      ],
      index: true,
    },
    speed_recorded: {
      type: Number,
      default: null,
    },
    primary_fine: {
      type: Number,
      required: true,
    },
    secondary_fine: {
      type: Number,
      default: 0,
    },
    total_fine: {
      type: Number,
      required: true,
    },
    snapshot_path: {
      type: String,
      default: '',
    },
    challan_status: {
      type: String,
      enum: ['ISSUED', 'PAID', 'DISPUTED', 'CANCELLED'],
      default: 'ISSUED',
      index: true,
    },
    review_status: {
      type: String,
      enum: ['PENDING', 'CONFIRMED', 'REJECTED'],
      default: 'PENDING',
      index: true,
    },
    sms_status: {
      type: String,
      enum: ['SIMULATED', 'DELIVERED', 'FAILED', 'PENDING'],
      default: 'SIMULATED',
    },
    details: {
      type: String,
      default: '',
    },
    source_video: {
      type: String,
      default: 'sample_traffic.mp4',
    },
    confidence: {
      type: Number,
      default: 0.92,
    },
    plate_box: {
      type: [Number],
      default: null,
    },
    plate_confidence: {
      type: Number,
      default: 0.0,
    },
    plate_status: {
      type: String,
      enum: ['DETECTED_READ', 'DETECTED_UNREADABLE', 'NO_PLATE', 'UNREADABLE'],
      default: 'DETECTED_READ',
    },
    raw_ocr_text: {
      type: String,
      default: '',
    },
    verification_status: {
      type: String,
      enum: ['VERIFIED_ANPR', 'UNVERIFIED_MANUAL_REVIEW', 'PENDING_AUDIT'],
      default: 'PENDING_AUDIT',
    },
  },
  { timestamps: true }
);

export const Violation = mongoose.model('Violation', violationSchema);
