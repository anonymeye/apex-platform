"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuth } from "@/lib/hooks/useAuth"
import { usePermissions } from "@/lib/hooks/usePermissions"
import type { UserRole } from "@/lib/store/authStore"

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
  requiredRole?: UserRole
  requiredAnyRole?: UserRole[]
  fallback?: React.ReactNode
  redirectTo?: string
}

export function ProtectedRoute({
  children,
  requiredPermission,
  requiredRole,
  requiredAnyRole,
  fallback,
  redirectTo = "/login",
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const { hasPermission, hasRole, hasAnyRole } = usePermissions()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo)
    }
  }, [isAuthenticated, isLoading, router, redirectTo])

  if (isLoading) {
    return fallback || <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return fallback || null
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return fallback || <AccessDenied />
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return fallback || <AccessDenied />
  }

  if (requiredAnyRole && !hasAnyRole(requiredAnyRole)) {
    return fallback || <AccessDenied />
  }

  return <>{children}</>
}

function AccessDenied() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Access Denied</h1>
        <p className="mt-2 text-gray-600">You don&apos;t have permission to access this resource.</p>
      </div>
    </div>
  )
}
