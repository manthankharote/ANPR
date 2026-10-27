import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import path from 'path';
import { ENV } from './config/env.js';
import { getDBStatus } from './config/db.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';

import authRoutes from './routes/authRoutes.js';
import dashboardRoutes from './routes/dashboardRoutes.js';
import vehicleRoutes from './routes/vehicleRoutes.js';
import violationRoutes from './routes/violationRoutes.js';
import aiRoutes from './routes/aiRoutes.js';
import settingsRoutes from './routes/settingsRoutes.js';

const app = express();

// Middleware
app.use(
  cors({
    origin: '*',
    credentials: true,
  })
);
app.use(express.json({ limit: '25mb' }));
app.use(express.urlencoded({ extended: true, limit: '25mb' }));
app.use(morgan('dev'));

// Static File Storage Serving (Evidence snapshots and uploaded videos)
app.use('/uploads', express.static(ENV.UPLOAD_DIR));
app.use('/evidence', express.static(ENV.EVIDENCE_DIR));

// System Health Endpoint
app.get('/api/health', (req, res) => {
  const dbStatus = getDBStatus();
  res.json({
    status: 'ONLINE',
    service: 'Traffic Sentinel Express Backend',
    timestamp: new Date().toISOString(),
    database: dbStatus,
    storage: {
      uploads: '/uploads',
      evidence: '/evidence',
      configured: true,
    },
    version: '2.0.0',
  });
});

// Mount REST API Routes
app.use('/api/auth', authRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/vehicles', vehicleRoutes);
app.use('/api/violations', violationRoutes);
app.use('/api/ai', aiRoutes);
app.use('/api/settings', settingsRoutes);

// Error Handling
app.use(notFoundHandler);
app.use(errorHandler);

export default app;
