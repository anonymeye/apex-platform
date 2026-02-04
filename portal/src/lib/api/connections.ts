import { apiClient } from "./client"
import type { Connection, ConnectionCreate } from "@/lib/types/model"

export const connectionsApi = {
  list: () => apiClient.get<Connection[]>("/connections"),
  create: (data: ConnectionCreate) => apiClient.post<Connection>("/connections", data),
  get: (id: string) => apiClient.get<Connection>(`/connections/${id}`),
  update: (id: string, data: Partial<ConnectionCreate>) => apiClient.put<Connection>(`/connections/${id}`, data),
  delete: (id: string) => apiClient.delete(`/connections/${id}`),
}

