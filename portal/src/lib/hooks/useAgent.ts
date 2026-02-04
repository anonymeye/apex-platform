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
    queryFn: async () => {
      try {
        const response = await agentsApi.list()
        return response.data
      } catch (error: any) {
        // Handle 404 as empty array (no agents yet)
        if (error?.response?.status === 404) {
          return []
        }
        throw error
      }
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 (no agents is a valid state)
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}
