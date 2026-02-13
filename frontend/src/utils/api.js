import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export const sendMessage = async (sessionId, message, context = {}) => {
  const response = await api.post('/api/chat', {
    session_id: sessionId,
    message,
    context,
  });
  return response.data;
};

// Tax Calculation API
export const calculateTax = async (totalIncome, deductions, regime = 'new') => {
  const response = await api.post('/api/calculate-tax', {
    total_income: totalIncome,
    deductions,
    regime,
  });
  return response.data;
};

// Regime Recommendation API
export const recommendRegime = async (grossIncome, deductions) => {
  const response = await api.post('/api/recommend-regime', null, {
    params: {
      gross_income: grossIncome,
    },
    data: deductions,
  });
  return response.data;
};

// ITR Form Recommendation API
export const recommendITRForm = async (profile, income) => {
  const response = await api.post('/api/recommend-itr-form', {
    profile,
    income,
  });
  return response.data;
};

// Get conversation history
export const getConversationHistory = async (sessionId) => {
  const response = await api.get(`/api/session/${sessionId}/history`);
  return response.data;
};

// Clear session
export const clearSession = async (sessionId) => {
  const response = await api.delete(`/api/session/${sessionId}`);
  return response.data;
};

// Get tax slabs
export const getTaxSlabs = async () => {
  const response = await api.get('/api/tax-info/slabs');
  return response.data;
};

// Get deductions info
export const getDeductionsInfo = async () => {
  const response = await api.get('/api/tax-info/deductions');
  return response.data;
};

// Get full forms
export const getFullForms = async () => {
  const response = await api.get('/api/full-forms');
  return response.data;
};

// Upload and analyze payslip
export const uploadPayslip = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/upload-payslip', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/');
  return response.data;
};

export default api;
