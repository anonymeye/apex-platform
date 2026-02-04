import { apiClient } from "./client"

export const chatApi = {
  /** Send a message; pass conversationId to continue a conversation (backend stores history in Redis). */
  sendMessage: (agentId: string, message: string, conversationId?: string | null) =>
    apiClient.post(`/agents/${agentId}/chat`, {
      message,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),

  getHistory: (agentId: string, conversationId?: string) =>
    apiClient.get(`/agents/${agentId}/chat`, {
      params: { conversation_id: conversationId },
    }),

  /** Clear conversation state on the backend (Redis). Call when user clears chat. */
  clearConversation: (agentId: string, conversationId: string) =>
    apiClient.delete(`/agents/${agentId}/conversations/${conversationId}`),

  /** Get conversation state from Redis (for debug panel). */
  getConversationState: (agentId: string, conversationId: string) =>
    apiClient.get<ConversationStateResponse>(
      `/agents/${agentId}/conversations/${conversationId}/state`
    ),
}

export type ConversationStateMetadata = {
  conversation_id: string
  user_id: string
  agent_id: string
  created_at: string
  last_activity_at: string
  message_count: number
}

export type ConversationStateResponse = {
  messages: Array<Record<string, unknown>>
  metadata: ConversationStateMetadata
}
