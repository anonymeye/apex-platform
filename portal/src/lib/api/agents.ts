import { apiClient } from "./client"
import type { Agent, AgentCreate, AgentUpdate } from "@/lib/types/agent"

export const agentsApi = {
  list: () => apiClient.get<Agent[]>("/agents"),
  get: (id: string) => apiClient.get<Agent>(`/agents/${id}`),
  create: (data: AgentCreate) => apiClient.post<Agent>("/agents", data),
  update: (id: string, data: AgentUpdate) => apiClient.put<Agent>(`/agents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/agents/${id}`),
}
