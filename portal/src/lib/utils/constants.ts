// Application constants

export const API_ENDPOINTS = {
  AGENTS: "/agents",
  CHAT: "/chat",
  KNOWLEDGE: "/knowledge",
  SCHEMAS: "/schemas",
  PLAYBOOKS: "/playbooks",
  TOOLS: "/tools",
  FINE_TUNING: "/fine-tuning",
  EXPERIMENTS: "/experiments",
  MONITORING: "/monitoring",
} as const

export const STORAGE_KEYS = {
  AUTH_TOKEN: "apex_token",
  AUTH_STORAGE: "auth-storage",
} as const
