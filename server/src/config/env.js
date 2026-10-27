import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env from root or server
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config();

export const ENV = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: process.env.NODE_ENV || 'development',
  CLIENT_URL: process.env.CLIENT_URL || 'http://localhost:5173',
  JWT_SECRET: process.env.JWT_SECRET || 'traffic_sentinel_jwt_secret_2026',
  MONGODB_URI: process.env.MONGODB_URI || 'mongodb://localhost:27017/traffic_sentinel',
  AI_SERVICE_URL: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  UPLOAD_DIR: path.resolve(__dirname, '../../../storage/uploads'),
  EVIDENCE_DIR: path.resolve(__dirname, '../../../storage/evidence'),
};
