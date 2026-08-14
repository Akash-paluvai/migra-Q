import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export const submitMigration = async (data) => {
  const res = await api.post('/migrations/', data);
  return res.data;
};

export const runValidation = async (migrationId) => {
  const res = await api.post(`/validation/${migrationId}/run`);
  return res.data;
};

export const triggerRepair = async (migrationId) => {
  const res = await api.post(`/repairs/${migrationId}/repair`);
  return res.data;
};

export const getScorecard = async (migrationId) => {
  const res = await api.get(`/reports/${migrationId}/scorecard`);
  return res.data;
};
