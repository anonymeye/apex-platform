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
}
