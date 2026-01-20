// Chat types

export interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: string
  tool_calls?: ToolCall[]
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  result?: unknown
}

export interface Conversation {
  id: string
  agent_id: string
  messages: Message[]
  created_at: string
  updated_at: string
}
