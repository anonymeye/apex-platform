import { apiClient } from "./client"
import type { User } from "../store/authStore"

export interface RegisterData {
  email: string
  password: string
  name?: string
  organization_name?: string
}

export interface LoginData {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface SwitchOrgData {
  org_id: string
}

export const authApi = {
  /**
   * Register a new user
   */
  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/register", data)
    return response.data
  },

  /**
   * Login user
   */
  login: async (data: LoginData): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/login", data)
    return response.data
  },

  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me")
    return response.data
  },

  /**
   * Switch active organization
   */
  switchOrganization: async (orgId: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/switch-org", {
      org_id: orgId,
    })
    return response.data
  },

  /**
   * Refresh token (if implemented)
   */
  refreshToken: async (): Promise<{ access_token: string }> => {
    const response = await apiClient.post<{ access_token: string }>("/auth/refresh")
    return response.data
  },
}
