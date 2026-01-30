import { apiClient } from "./client"
import type { Tool, ToolCreate, ToolUpdate } from "@/lib/types/tools"

export const toolsApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<Tool[]>("/tools", { params: params ?? {} }),
  get: (id: string) => apiClient.get<Tool>(`/tools/${id}`),
  create: (data: ToolCreate) => apiClient.post<Tool>("/tools", data),
  update: (id: string, data: ToolUpdate) => apiClient.put<Tool>(`/tools/${id}`, data),
  delete: (id: string) => apiClient.delete(`/tools/${id}`),
}
