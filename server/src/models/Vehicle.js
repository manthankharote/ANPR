import mongoose from 'mongoose';

const vehicleSchema = new mongoose.Schema(
  {
    plate_number: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      uppercase: true,
      index: true,
    },
    owner_name: {
      type: String,
      required: true,
      trim: true,
    },
    vehicle_model: {
      type: String,
      required: true,
    },
    vehicle_type: {
      type: String,
      enum: ['Car', 'Motorcycle', 'Truck', 'Bus', 'Bicycle', 'Other'],
      default: 'Car',
    },
    insurance_expiry: {
      type: String,
      required: true,
    },
    insurance_status: {
      type: String,
      enum: ['VALID', 'EXPIRED'],
      default: 'VALID',
    },
    puc_expiry: {
      type: String,
      required: true,
    },
    puc_status: {
      type: String,
      enum: ['VALID', 'EXPIRED'],
      default: 'VALID',
    },
    registered_rto: {
      type: String,
      required: true,
    },
    mobile_number: {
      type: String,
      required: true,
    },
  },
  { timestamps: true }
);

export const Vehicle = mongoose.model('Vehicle', vehicleSchema);
