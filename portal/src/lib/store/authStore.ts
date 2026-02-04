import { create } from "zustand"
import { persist } from "zustand/middleware"

export type UserRole =
  | "super_admin"
  | "org_admin"
  | "agent_builder"
  | "content_manager"
  | "analyst"
  | "end_user"

export interface Organization {
  id: string
  name: string
  role: UserRole
}

export interface User {
  id: string
  email: string
  name?: string
  isSuperAdmin: boolean
  currentOrgId: string
  currentOrgName?: string
  currentRole: UserRole
  permissions: string[]
  organizations: Organization[]
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
  updateUser: (user: Partial<User>) => void
  switchOrganization: (orgId: string, orgName: string, role: UserRole) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      setAuth: (user, token) => {
        localStorage.setItem("apex_token", token)
        set({ user, token, isAuthenticated: true, isLoading: false })
      },
      clearAuth: () => {
        localStorage.removeItem("apex_token")
        set({ user: null, token: null, isAuthenticated: false, isLoading: false })
      },
      updateUser: (userUpdate) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userUpdate } : null,
        }))
      },
      switchOrganization: (orgId, orgName, role) => {
        set((state) => ({
          user: state.user
            ? {
                ...state.user,
                currentOrgId: orgId,
                currentOrgName: orgName,
                currentRole: role,
              }
            : null,
        }))
      },
    }),
    {
      name: "auth-storage",
    }
  )
)
