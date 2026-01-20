import { apiClient } from "./client"

export const experimentsApi = {
  list: () => apiClient.get("/experiments"),
  get: (id: string) => apiClient.get(`/experiments/${id}`),
  create: (data: unknown) => apiClient.post("/experiments", data),
  compare: (ids: string[]) =>
    apiClient.post("/experiments/compare", { experiment_ids: ids }),
  getMetrics: (id: string) => apiClient.get(`/experiments/${id}/metrics`),
}
