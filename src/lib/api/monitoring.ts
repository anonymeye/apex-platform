import { apiClient } from "./client"

export const monitoringApi = {
  getMetrics: (agentId?: string) =>
    apiClient.get("/monitoring/metrics", { params: { agent_id: agentId } }),
  getLogs: (params?: { agent_id?: string; limit?: number; offset?: number }) =>
    apiClient.get("/monitoring/logs", { params }),
  getToolUsage: (agentId?: string) =>
    apiClient.get("/monitoring/tool-usage", { params: { agent_id: agentId } }),
}
