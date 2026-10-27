import express from 'express';
import {
  processVideo,
  processSampleVideo,
  getJobStatus,
  getSignalState,
  overrideSignal,
} from '../controllers/aiController.js';
import { uploadVideo } from '../middleware/uploadMiddleware.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

router.post('/process-video', requireAuth, uploadVideo.single('video'), processVideo);
router.post('/process-sample', requireAuth, processSampleVideo);
router.get('/jobs/:jobId', requireAuth, getJobStatus);
router.get('/signal/state', getSignalState);
router.post('/signal/override', requireAuth, overrideSignal);

export default router;
