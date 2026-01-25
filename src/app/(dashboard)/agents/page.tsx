"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Bot, Loader2, Pencil } from "lucide-react"
import { agentsApi } from "@/lib/api/agents"
import type { Agent } from "@/lib/types/agent"
import { useAgentStore } from "@/lib/store/agentStore"

export default function AgentsPage() {
  const { setSelectedAgent } = useAgentStore()

  const { data: agents, isLoading, error } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      try {
        const response = await agentsApi.list()
        return response.data
      } catch (error: any) {
        if (error?.response?.status === 404) {
          return []
        }
        throw error
      }
    },
  })

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground">
            Manage your AI agents
          </p>
        </div>
        <Button asChild>
          <Link href="/agents/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Agent
          </Link>
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load agents. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && (!agents || agents.length === 0) && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first agent to get started
              </p>
              <Button asChild>
                <Link href="/agents/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Agent
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && agents && agents.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card
              key={agent.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleSelectAgent(agent)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={(e) => {
                      e.stopPropagation()
                    }}
                    asChild
                  >
                    <Link href={`/agents/${agent.id}/edit`}>
                      <Pencil className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
                {agent.description && (
                  <CardDescription className="mt-2">
                    {agent.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Model:</span>
                    <span className="font-medium">
                      {agent.model_ref?.connection?.name
                        ? `${agent.model_ref.connection.name} / ${agent.model_ref.name}`
                        : agent.model_ref_id}
                    </span>
                  </div>
                  {agent.tools && agent.tools.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Tools:</span>
                      <span className="font-medium">{agent.tools.length}</span>
                    </div>
                  )}
                  {agent.max_iterations && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Max Iterations:</span>
                      <span className="font-medium">{agent.max_iterations}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
