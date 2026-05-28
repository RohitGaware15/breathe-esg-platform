import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Inject token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

// Auth
export const login = (username, password) =>
  api.post('/api/auth/login/', { username, password })

export const logout = () => api.post('/auth/logout/')

export const getMe = () => api.get('/auth/me/')

// Tenants
export const getTenants = () => api.get('/tenants/')

// Ingestion
export const uploadFile = (formData) =>
  api.post('/ingestion/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getBatches = (params = {}) =>
  api.get('/ingestion/batches/', { params })

// Normalized records
export const getRecords = (params = {}) =>
  api.get('/normalization/records/', { params })

// Review
export const approveRecord = (id, comment = '') =>
  api.post(`/review/records/${id}/approve/`, { comment })

export const flagRecord = (id, comment = '') =>
  api.post(`/review/records/${id}/flag/`, { comment })

export const rejectRecord = (id, comment = '') =>
  api.post(`/review/records/${id}/reject/`, { comment })

export const getReviewSummary = (tenantId) =>
  api.get('/review/records/summary/', { params: { tenant_id: tenantId } })

export default api
