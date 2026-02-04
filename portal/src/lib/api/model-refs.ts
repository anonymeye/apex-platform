import { apiClient } from "./client"
import type { ModelRef, ModelRefCreate } from "@/lib/types/model"

export const modelRefsApi = {
  list: () => apiClient.get<ModelRef[]>("/model-refs"),
  create: (data: ModelRefCreate) => apiClient.post<ModelRef>("/model-refs", data),
  get: (id: string) => apiClient.get<ModelRef>(`/model-refs/${id}`),
  update: (id: string, data: Partial<ModelRefCreate>) => apiClient.put<ModelRef>(`/model-refs/${id}`, data),
  delete: (id: string) => apiClient.delete(`/model-refs/${id}`),
}

