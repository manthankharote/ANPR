import { dataStore } from '../services/dataStore.js';

export const getVehicles = async (req, res, next) => {
  try {
    const { plate, limit } = req.query;
    const vehicles = await dataStore.getVehicles({ plate, limit: Number(limit) || 100 });
    return res.json({
      success: true,
      count: vehicles.length,
      data: vehicles,
    });
  } catch (error) {
    next(error);
  }
};

export const getVehicleByPlate = async (req, res, next) => {
  try {
    const { plate } = req.params;
    const vehicle = await dataStore.getVehicleByPlate(plate);
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        message: `Vehicle with registration plate '${plate}' was not found in the VAHAN mock database.`,
      });
    }

    return res.json({
      success: true,
      data: vehicle,
    });
  } catch (error) {
    next(error);
  }
};

export const createVehicle = async (req, res, next) => {
  try {
    const { plate_number, owner_name, vehicle_model, vehicle_type, insurance_status, insurance_expiry, puc_status, puc_expiry, registered_rto, mobile_number } = req.body;

    if (!plate_number || !owner_name) {
      return res.status(400).json({
        success: false,
        message: 'Plate number and owner name are mandatory fields.',
      });
    }

    const cleanPlate = plate_number.replace(/\s+/g, '').toUpperCase();

    const newVehicle = await dataStore.createVehicle({
      plate_number: cleanPlate,
      owner_name,
      vehicle_model: vehicle_model || 'Standard Motor Vehicle',
      vehicle_type: vehicle_type || 'Car',
      insurance_status: insurance_status || 'VALID',
      insurance_expiry: insurance_expiry || '2027-10-26',
      puc_status: puc_status || 'VALID',
      puc_expiry: puc_expiry || '2027-10-26',
      registered_rto: registered_rto || 'State Transport Department',
      mobile_number: mobile_number || '+919800000000',
    });

    return res.status(201).json({
      success: true,
      message: 'Vehicle registered successfully in VAHAN repository.',
      data: newVehicle,
    });
  } catch (error) {
    next(error);
  }
};
