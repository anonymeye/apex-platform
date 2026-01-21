import { useAuth } from "./useAuth"
import type { UserRole } from "../store/authStore"

/**
 * Hook for checking user permissions and roles
 */
export function usePermissions() {
  const { user } = useAuth()

  /**
   * Check if user has a specific permission
   */
  const hasPermission = (permission: string): boolean => {
    if (!user) return false
    if (user.isSuperAdmin) return true
    if (user.permissions.includes("*")) return true

    // Check exact match
    if (user.permissions.includes(permission)) return true

    // Check resource wildcard (e.g., "agents:create" matches "agents:*")
    const [resource] = permission.split(":", 1)
    if (user.permissions.includes(`${resource}:*`)) return true

    return false
  }

  /**
   * Check if user has any of the specified permissions
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some((p) => hasPermission(p))
  }

  /**
   * Check if user has all of the specified permissions
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every((p) => hasPermission(p))
  }

  /**
   * Check if user has a specific role
   */
  const hasRole = (role: UserRole): boolean => {
    return user?.currentRole === role
  }

  /**
   * Check if user has any of the specified roles
   */
  const hasAnyRole = (roles: UserRole[]): boolean => {
    if (!user) return false
    return roles.includes(user.currentRole)
  }

  /**
   * Check if user is super admin
   */
  const isSuperAdmin = (): boolean => {
    return user?.isSuperAdmin ?? false
  }

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    isSuperAdmin,
    permissions: user?.permissions || [],
    role: user?.currentRole,
    user,
  }
}
