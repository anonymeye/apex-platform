import { create } from "zustand"
import { persist } from "zustand/middleware"

interface User {
  id: string
  email: string
  name?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => {
        localStorage.setItem("apex_token", token)
        set({ user, token, isAuthenticated: true })
      },
      clearAuth: () => {
        localStorage.removeItem("apex_token")
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    {
      name: "auth-storage",
    }
  )
)
