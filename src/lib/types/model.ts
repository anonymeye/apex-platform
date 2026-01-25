export interface Connection {
  id: string
  name: string
  connection_type: string
  provider: string
  base_url?: string | null
  auth_type: string
  api_key_env_var?: string | null
  config?: Record<string, any> | null
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ModelRef {
  id: string
  name: string
  runtime_id: string
  connection_id: string
  connection?: Connection | null
  config?: Record<string, any> | null
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ConnectionCreate {
  name: string
  connection_type: string
  provider: string
  base_url?: string
  auth_type: string
  api_key_env_var?: string
  config?: Record<string, any>
}

export interface ModelRefCreate {
  name: string
  runtime_id: string
  connection_id: string
  config?: Record<string, any>
}

