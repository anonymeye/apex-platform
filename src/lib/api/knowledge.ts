import { apiClient } from "./client"

export const knowledgeApi = {
  list: () => apiClient.get("/knowledge"),
  get: (id: string) => apiClient.get(`/knowledge/${id}`),
  upload: (formData: FormData) =>
    apiClient.post("/knowledge/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (id: string) => apiClient.delete(`/knowledge/${id}`),
}
