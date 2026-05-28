import axios from 'axios'

// Backend URL from Vercel environment variable
// Example:
// VITE_API_URL=https://breathe-esg-backend-fdkp.onrender.com
const BASE_URL = import.meta.env.VITE_API_URL

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach auth token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')

  if (token) {
    config.headers.Authorization = `Token ${token}`
  }

  return config
})

// =========================
// AUTH
// =========================

export const login = (username, password) =>
  api.post('/api/auth/login/', {
    username,
    password,
  })

export const logout = () =>
  api.post('/api/auth/logout/')

export const getMe = () =>
  api.get('/api/auth/me/')

// =========================
// TENANTS
// =========================

export const getTenants = () =>
  api.get('/api/tenants/')

// =========================
// INGESTION
// =========================

export const uploadFile = (formData) =>
  api.post('/api/ingestion/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

export const getBatches = (params = {}) =>
  api.get('/api/ingestion/batches/', {
    params,
  })

// =========================
// NORMALIZATION
// =========================

export const getRecords = (params = {}) =>
  api.get('/api/normalization/records/', {
    params,
  })

// =========================
// REVIEW
// =========================

export const approveRecord = (id, comment = '') =>
  api.post(`/api/review/records/${id}/approve/`, {
    comment,
  })

export const flagRecord = (id, comment = '') =>
  api.post(`/api/review/records/${id}/flag/`, {
    comment,
  })

export const rejectRecord = (id, comment = '') =>
  api.post(`/api/review/records/${id}/reject/`, {
    comment,
  })

export const getReviewSummary = (tenantId) =>
  api.get('/api/review/records/summary/', {
    params: {
      tenant_id: tenantId,
    },
  })

export default api
