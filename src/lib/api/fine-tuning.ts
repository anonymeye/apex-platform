import { apiClient } from "./client"

export const fineTuningApi = {
  list: () => apiClient.get("/fine-tuning"),
  get: (id: string) => apiClient.get(`/fine-tuning/${id}`),
  create: (data: unknown) => apiClient.post("/fine-tuning", data),
  cancel: (id: string) => apiClient.post(`/fine-tuning/${id}/cancel`),
  getProgress: (id: string) => apiClient.get(`/fine-tuning/${id}/progress`),
}
