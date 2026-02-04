import { apiClient } from "./client"

export const schemasApi = {
  list: () => apiClient.get("/schemas"),
  get: (id: string) => apiClient.get(`/schemas/${id}`),
  create: (data: unknown) => apiClient.post("/schemas", data),
  update: (id: string, data: unknown) => apiClient.put(`/schemas/${id}`, data),
  delete: (id: string) => apiClient.delete(`/schemas/${id}`),
  analyze: (schema: unknown) => apiClient.post("/schemas/analyze", { schema }),
}
