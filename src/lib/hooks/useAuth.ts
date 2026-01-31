import { useCallback } from "react"
import { authApi } from "../api/auth"
import { useAuthStore, type User } from "../store/authStore"

export function useAuth() {
  const { user, token, isAuthenticated, isLoading, setAuth, clearAuth, updateUser, switchOrganization } =
    useAuthStore()

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        const response = await authApi.login({ email, password })
        setAuth(response.user, response.access_token)
        return response
      } catch (error) {
        throw error
      }
    },
    [setAuth]
  )

  const register = useCallback(
    async (email: string, password: string, name?: string, organizationName?: string) => {
      try {
        const response = await authApi.register({ email, password, name, organization_name: organizationName })
        setAuth(response.user, response.access_token)
        return response
      } catch (error) {
        throw error
      }
    },
    [setAuth]
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore: still clear local auth so user is not stuck
    }
    clearAuth()
  }, [clearAuth])

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.getCurrentUser()
      updateUser(userData)
      return userData
    } catch (error) {
      // If refresh fails, user might be logged out
      clearAuth()
      throw error
    }
  }, [updateUser, clearAuth])

  const switchOrg = useCallback(
    async (orgId: string) => {
      try {
        const response = await authApi.switchOrganization(orgId)
        setAuth(response.user, response.access_token)
        return response
      } catch (error) {
        throw error
      }
    },
    [setAuth]
  )

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
    switchOrg,
    switchOrganization, // Direct state update (for optimistic updates)
  }
}
