import express from 'express';
import { getSettings, updateSettings, testNotice } from '../controllers/settingsController.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

router.get('/', requireAuth, getSettings);
router.put('/', requireAuth, updateSettings);
router.post('/test-notice', requireAuth, testNotice);

export default router;
