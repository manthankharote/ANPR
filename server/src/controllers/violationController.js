import { dataStore } from '../services/dataStore.js';

export const getViolations = async (req, res, next) => {
  try {
    const { plate, type, status, limit } = req.query;
    const violations = await dataStore.getViolations({
      plate,
      type,
      status,
      limit: Number(limit) || 100,
    });

    return res.json({
      success: true,
      count: violations.length,
      data: violations,
    });
  } catch (error) {
    next(error);
  }
};

export const getViolationById = async (req, res, next) => {
  try {
    const { id } = req.params;
    const violation = await dataStore.getViolationById(id);
    if (!violation) {
      return res.status(404).json({
        success: false,
        message: `Violation record #${id} not found.`,
      });
    }

    return res.json({
      success: true,
      data: violation,
    });
  } catch (error) {
    next(error);
  }
};

export const reviewViolation = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { review_status, challan_status } = req.body;

    const updates = {};
    if (review_status) updates.review_status = review_status;
    if (challan_status) updates.challan_status = challan_status;

    const updated = await dataStore.updateViolationReview(id, updates);
    if (!updated) {
      return res.status(404).json({
        success: false,
        message: `Violation record #${id} not found for review update.`,
      });
    }

    return res.json({
      success: true,
      message: `Violation #${id} review updated successfully.`,
      data: updated,
    });
  } catch (error) {
    next(error);
  }
};
