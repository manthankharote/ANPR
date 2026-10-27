import mongoose from 'mongoose';

const processingJobSchema = new mongoose.Schema(
  {
    job_id: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    status: {
      type: String,
      enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'],
      default: 'PENDING',
      index: true,
    },
    filename: {
      type: String,
      required: true,
    },
    original_name: {
      type: String,
      default: '',
    },
    progress: {
      type: Number,
      default: 0,
    },
    total_frames: {
      type: Number,
      default: 0,
    },
    violations_detected: {
      type: Number,
      default: 0,
    },
    results: {
      type: Array,
      default: [],
    },
    error_message: {
      type: String,
      default: null,
    },
  },
  { timestamps: true }
);

export const ProcessingJob = mongoose.model('ProcessingJob', processingJobSchema);
