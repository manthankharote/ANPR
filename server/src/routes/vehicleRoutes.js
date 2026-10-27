import express from 'express';
import { getVehicles, getVehicleByPlate, createVehicle } from '../controllers/vehicleController.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

router.get('/', requireAuth, getVehicles);
router.get('/:plate', requireAuth, getVehicleByPlate);
router.post('/', requireAuth, createVehicle);

export default router;
