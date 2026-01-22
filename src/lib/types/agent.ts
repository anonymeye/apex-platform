// Agent types

export interface Agent {
  id: string
  name: string
  description?: string
  system_message?: string
  persona?: string
  tone?: string
  model_id?: string
  status: "active" | "inactive" | "training"
  created_at: string
  updated_at: string
}

export interface AgentConfig {
  system_message?: string
  persona?: string
  tone?: string
  max_iterations?: number
  temperature?: number
}
