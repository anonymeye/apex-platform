import { apiClient } from "./client"

export const playbooksApi = {
  list: () => apiClient.get("/playbooks"),
  get: (id: string) => apiClient.get(`/playbooks/${id}`),
  create: (data: unknown) => apiClient.post("/playbooks", data),
  update: (id: string, data: unknown) => apiClient.put(`/playbooks/${id}`, data),
  delete: (id: string) => apiClient.delete(`/playbooks/${id}`),
}
