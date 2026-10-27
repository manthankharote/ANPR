import { dataStore } from '../services/dataStore.js';

export const getDashboardStats = async (req, res, next) => {
  try {
    const stats = await dataStore.getDashboardStats();
    return res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    next(error);
  }
};
