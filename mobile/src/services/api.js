import axios from 'axios'
import { Platform } from 'react-native'
import AsyncStorage from '@react-native-async-storage/async-storage'

// Platform-specific API URL
const API_BASE = Platform.select({
  ios: 'http://localhost:8000',
  android: 'http://10.0.2.2:8000', // Android emulator
  web: 'http://localhost:8000',
  default: process.env.EXPO_PUBLIC_API_URL || 'https://api.blackroad.com'
})

console.log('API Base URL:', API_BASE)

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('userToken')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (error) {
      console.error('Error reading token:', error)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, clear storage
      await AsyncStorage.removeItem('userToken')
      // Could trigger logout here
    }
    
    // Format error message
    const message = error.response?.data?.message || error.message || 'An error occurred'
    const errorObj = new Error(message)
    errorObj.status = error.response?.status
    errorObj.data = error.response?.data
    
    return Promise.reject(errorObj)
  }
)

// API methods
export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  logout: () =>
    api.post('/auth/logout'),
  getProfile: () =>
    api.get('/auth/profile'),
}

export const billingAPI = {
  getUsage: () =>
    api.get('/billing/usage'),
  getSubscription: () =>
    api.get('/billing/subscription'),
  getInvoices: () =>
    api.get('/billing/invoices'),
  getForecast: () =>
    api.get('/billing/forecast'),
  upgrade: (plan) =>
    api.post('/billing/upgrade', { plan }),
}

export const analyticsAPI = {
  getDashboard: () =>
    api.get('/admin/dashboard'),
  getRevenue: () =>
    api.get('/admin/revenue'),
  getChurnPrediction: () =>
    api.get('/ml/churn-prediction'),
  getLTVForecast: () =>
    api.get('/ml/ltv-forecast'),
  getCohortAnalysis: () =>
    api.get('/ml/cohort-analysis'),
  getSegmentation: () =>
    api.get('/customer-analytics/segmentation'),
  getInsights: () =>
    api.get('/customer-analytics/insights'),
}

export default api
