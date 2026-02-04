/** Tool types for the top-level tools API (org-scoped). */

export interface Tool {
  id: string
  name: string
  description: string
  tool_type: string
  knowledge_base_id?: string | null
  config?: Record<string, unknown> | null
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ToolCreate {
  name: string
  description: string
  tool_type: string
  knowledge_base_id?: string | null
  config?: Record<string, unknown>
}

export interface ToolUpdate {
  name?: string
  description?: string
  config?: Record<string, unknown>
}
