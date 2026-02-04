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
      const tokenKey = process.env.NEXT_PUBLIC_JWT_STORAGE_KEY || "apex_token"
      localStorage.removeItem(tokenKey)
      
      // Only redirect if we're in the browser and not already on login/register
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/register")) {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)
