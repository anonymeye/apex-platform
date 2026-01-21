"use client"

import { usePermissions } from "@/lib/hooks/usePermissions"
import type { UserRole } from "@/lib/store/authStore"

interface PermissionGateProps {
  children: React.ReactNode
  permission?: string
  permissions?: string[] // Requires ALL
  anyPermission?: string[] // Requires ANY
  role?: UserRole
  anyRole?: UserRole[]
  fallback?: React.ReactNode
}

/**
 * Component that conditionally renders children based on user permissions/roles.
 * Use this to show/hide UI elements based on permissions.
 */
export function PermissionGate({
  children,
  permission,
  permissions,
  anyPermission,
  role,
  anyRole,
  fallback = null,
}: PermissionGateProps) {
  const { hasPermission, hasAllPermissions, hasAnyPermission, hasRole, hasAnyRole } =
    usePermissions()

  // Check permissions
  if (permission && !hasPermission(permission)) {
    return <>{fallback}</>
  }

  if (permissions && !hasAllPermissions(permissions)) {
    return <>{fallback}</>
  }

  if (anyPermission && !hasAnyPermission(anyPermission)) {
    return <>{fallback}</>
  }

  // Check roles
  if (role && !hasRole(role)) {
    return <>{fallback}</>
  }

  if (anyRole && !hasAnyRole(anyRole)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
