import express from 'express';
import { getViolations, getViolationById, reviewViolation } from '../controllers/violationController.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

router.get('/', requireAuth, getViolations);
router.get('/:id', requireAuth, getViolationById);
router.patch('/:id/review', requireAuth, reviewViolation);

export default router;
