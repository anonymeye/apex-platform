export interface KnowledgeBase {
  id: string
  name: string
  slug: string
  description?: string | null
  organization_id: string
  metadata?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseCreate {
  name: string
  description?: string | null
  metadata?: Record<string, any>
}

export interface KnowledgeBaseUpdate {
  name?: string
  description?: string | null
  metadata?: Record<string, any>
}

export interface Document {
  id: string
  knowledge_base_id: string
  content: string
  source?: string | null
  chunk_index?: number | null
  vector_id?: string | null
  metadata?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface DocumentUpload {
  content: string
  source?: string | null
  metadata?: Record<string, any>
}

export interface DocumentUploadRequest {
  documents: DocumentUpload[]
  auto_create_tool?: boolean
  auto_add_to_agent_id?: string | null
  chunk_size?: number
  chunk_overlap?: number
}

export interface DocumentUploadResponse {
  documents: Document[]
  tool_created?: {
    id: string
    name: string
    description: string
  } | null
  message: string
}

export interface Tool {
  id: string
  name: string
  description: string
  tool_type: string
  knowledge_base_id?: string | null
  config?: Record<string, any> | null
  rag_template?: string | null
  rag_k?: number | null
  auto_created: boolean
  organization_id: string
  created_at: string
  updated_at: string
}

export interface ToolUpdate {
  name?: string
  description?: string
  rag_template?: string | null
  rag_k?: number
}
