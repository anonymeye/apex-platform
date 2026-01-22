"use client"

import { useQuery } from "@tanstack/react-query"
import { Bot, ChevronDown, Plus, Check } from "lucide-react"
import { useAgentStore } from "@/lib/store/agentStore"
import { agentsApi } from "@/lib/api/agents"
import type { Agent } from "@/lib/types/agent"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils/cn"

export function AgentSelector() {
  const router = useRouter()
  const { selectedAgentId, selectedAgent, setSelectedAgent, clearSelection } =
    useAgentStore()

  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      try {
        const response = await agentsApi.list()
        return response.data as Agent[]
      } catch (error: any) {
        // Handle 404 as empty array (no agents yet)
        if (error?.response?.status === 404) {
          return [] as Agent[]
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

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent)
  }

  const handleCreateAgent = () => {
    router.push("/agents/new")
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-md border bg-muted/50">
        <Bot className="h-4 w-4 animate-pulse" />
        <span className="text-sm text-muted-foreground">Loading...</span>
      </div>
    )
  }

  if (!agents || agents.length === 0) {
    return (
      <Button
        onClick={handleCreateAgent}
        variant="outline"
        className="w-full justify-start"
      >
        <Plus className="mr-2 h-4 w-4" />
        Create Your First Agent
      </Button>
    )
  }

  const currentAgent = selectedAgent || agents.find((a) => a.id === selectedAgentId)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="w-full justify-between"
        >
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            <span className="text-sm font-medium">
              {currentAgent ? currentAgent.name : "Select Agent"}
            </span>
          </div>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[200px]">
        <DropdownMenuLabel>Agents</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {agents.map((agent) => (
          <DropdownMenuItem
            key={agent.id}
            onClick={() => handleSelectAgent(agent)}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "h-2 w-2 rounded-full",
                  agent.status === "active"
                    ? "bg-green-500"
                    : agent.status === "training"
                    ? "bg-yellow-500"
                    : "bg-gray-400"
                )}
              />
              <span>{agent.name}</span>
            </div>
            {selectedAgentId === agent.id && (
              <Check className="h-4 w-4" />
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleCreateAgent}>
          <Plus className="mr-2 h-4 w-4" />
          Create New Agent
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
