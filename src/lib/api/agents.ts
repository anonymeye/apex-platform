import { apiClient } from "./client"

export const agentsApi = {
  list: () => apiClient.get("/agents"),
  get: (id: string) => apiClient.get(`/agents/${id}`),
  create: (data: unknown) => apiClient.post("/agents", data),
  update: (id: string, data: unknown) => apiClient.put(`/agents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/agents/${id}`),
}
