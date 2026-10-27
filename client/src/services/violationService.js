import api from './api';

export const violationService = {
  getDashboardStats: async () => {
    const res = await api.get('/dashboard/stats');
    return res.data;
  },

  getViolations: async (params = {}) => {
    const res = await api.get('/violations', { params });
    return res.data;
  },

  getViolationById: async (id) => {
    const res = await api.get(`/violations/${id}`);
    return res.data;
  },

  reviewViolation: async (id, reviewData) => {
    const res = await api.patch(`/violations/${id}/review`, reviewData);
    return res.data;
  },

  getVehicles: async (params = {}) => {
    const res = await api.get('/vehicles', { params });
    return res.data;
  },

  getVehicleByPlate: async (plate) => {
    const res = await api.get(`/vehicles/${plate}`);
    return res.data;
  },

  createVehicle: async (vehicleData) => {
    const res = await api.post('/vehicles', vehicleData);
    return res.data;
  },

  processVideo: async (formData) => {
    const res = await api.post('/ai/process-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  processSampleVideo: async (payload = {}) => {
    const res = await api.post('/ai/process-sample', payload);
    return res.data;
  },

  getJobStatus: async (jobId) => {
    const res = await api.get(`/ai/jobs/${jobId}`);
    return res.data;
  },

  getSignalState: async () => {
    const res = await api.get('/ai/signal/state');
    return res.data;
  },

  overrideSignal: async (data) => {
    const res = await api.post('/ai/signal/override', data);
    return res.data;
  },

  getSettings: async () => {
    const res = await api.get('/settings');
    return res.data;
  },

  updateSettings: async (settings) => {
    const res = await api.put('/settings', settings);
    return res.data;
  },

  sendTestNotice: async (payload) => {
    const res = await api.post('/settings/test-notice', payload);
    return res.data;
  },
};
