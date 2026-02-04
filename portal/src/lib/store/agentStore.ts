import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Agent } from "@/lib/types/agent"

interface AgentState {
  selectedAgentId: string | null
  selectedAgent: Agent | null
  setSelectedAgent: (agent: Agent) => void
  setSelectedAgentId: (agentId: string) => void
  clearSelection: () => void
}

export const useAgentStore = create<AgentState>()(
  persist(
    (set) => ({
      selectedAgentId: null,
      selectedAgent: null,
      setSelectedAgent: (agent) =>
        set({ selectedAgentId: agent.id, selectedAgent: agent }),
      setSelectedAgentId: (agentId) =>
        set({ selectedAgentId: agentId, selectedAgent: null }),
      clearSelection: () =>
        set({ selectedAgentId: null, selectedAgent: null }),
    }),
    {
      name: "agent-storage",
    }
  )
)
