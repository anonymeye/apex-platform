import { apiClient } from "./client"

export const chatApi = {
  sendMessage: (agentId: string, message: string) =>
    apiClient.post(`/agents/${agentId}/chat`, { message }),
  getHistory: (agentId: string, conversationId?: string) =>
    apiClient.get(`/agents/${agentId}/chat`, {
      params: { conversation_id: conversationId },
    }),
}
