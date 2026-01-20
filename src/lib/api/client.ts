import axios from "axios"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || "v1"

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/${API_VERSION}`,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(process.env.NEXT_PUBLIC_JWT_STORAGE_KEY || "apex_token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - clear token and redirect to login
      localStorage.removeItem(process.env.NEXT_PUBLIC_JWT_STORAGE_KEY || "apex_token")
      // window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)
