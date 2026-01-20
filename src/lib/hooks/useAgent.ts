import { useQuery } from "@tanstack/react-query"
import { agentsApi } from "@/lib/api/agents"

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => agentsApi.get(agentId).then((res) => res.data),
    enabled: !!agentId,
  })
}

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => agentsApi.list().then((res) => res.data),
  })
}
