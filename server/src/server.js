import app from './app.js';
import { ENV } from './config/env.js';
import { connectDB } from './config/db.js';
import { seedMongoIfEmpty } from './services/dataStore.js';

const startServer = async () => {
  // Connect to Database (or activate resilient fallback)
  const dbConnected = await connectDB();
  if (dbConnected) {
    await seedMongoIfEmpty();
  }

  const server = app.listen(ENV.PORT, () => {
    console.log(`\n=======================================================`);
    console.log(` 🚦 TRAFFIC SENTINEL BACKEND ENGINE ONLINE`);
    console.log(` Server URL : http://localhost:${ENV.PORT}`);
    console.log(` Health API : http://localhost:${ENV.PORT}/api/health`);
    console.log(` Storage Dir: ${ENV.UPLOAD_DIR}`);
    console.log(` Environment: ${ENV.NODE_ENV}`);
    console.log(`=======================================================\n`);
  });

  process.on('SIGTERM', () => {
    console.log('SIGTERM received. Gracefully shutting down...');
    server.close(() => process.exit(0));
  });
};

startServer().catch((err) => {
  console.error('Fatal Server Boot Error:', err);
  process.exit(1);
});
