import { apiClient } from "./client"

export const toolsApi = {
  list: () => apiClient.get("/tools"),
  get: (id: string) => apiClient.get(`/tools/${id}`),
  create: (data: unknown) => apiClient.post("/tools", data),
  update: (id: string, data: unknown) => apiClient.put(`/tools/${id}`, data),
  delete: (id: string) => apiClient.delete(`/tools/${id}`),
}
