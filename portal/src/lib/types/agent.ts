// Agent types

export interface ToolInfo {
  id: string
  name: string
  description?: string
  tool_type: string
}

export interface ConnectionInfo {
  id: string
  name: string
  provider: string
  connection_type: string
}

export interface ModelRefInfo {
  id: string
  name: string
  runtime_id: string
  connection: ConnectionInfo
}

export interface Agent {
  id: string
  name: string
  description?: string
  model_ref_id: string
  model_ref?: ModelRefInfo | null
  system_message?: string
  max_iterations: number
  temperature?: number
  max_tokens?: number
  config?: Record<string, any>
  organization_id: string
  tools: ToolInfo[]
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  description?: string
  model_ref_id: string
  system_message?: string
  max_iterations?: number
  temperature?: number
  max_tokens?: number
  config?: Record<string, any>
  tool_ids?: string[]
}

export interface AgentUpdate {
  name?: string
  description?: string
  model_ref_id?: string
  system_message?: string
  max_iterations?: number
  temperature?: number
  max_tokens?: number
  config?: Record<string, any>
  tool_ids?: string[]
}

export interface AgentConfig {
  system_message?: string
  persona?: string
  tone?: string
  max_iterations?: number
  temperature?: number
}
