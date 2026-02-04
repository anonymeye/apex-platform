"use client"

import { useRouter, useParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { agentsApi } from "@/lib/api/agents"
import { connectionsApi } from "@/lib/api/connections"
import { modelRefsApi } from "@/lib/api/model-refs"
import { useToolsList } from "@/lib/hooks/useTools"
import { useAgentStore } from "@/lib/store/agentStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Combobox } from "@/components/ui/combobox"
import type { AgentUpdate } from "@/lib/types/agent"
import { useEffect } from "react"
import type { Connection, ModelRef } from "@/lib/types/model"

const agentSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name must be less than 255 characters"),
  description: z.string().optional(),
  system_message: z.string().optional(),
  max_iterations: z.number().min(1).max(50).optional(),
  temperature: z.number().min(0).max(2).optional(),
  max_tokens: z.number().min(1).optional(),
  connection_id: z.string().min(1, "Please select a connection"),
  model_ref_id: z.string().min(1, "Please select a model"),
  tool_ids: z.array(z.string()).optional(),
})

type AgentFormData = z.infer<typeof agentSchema>

function transformFormDataToApi(data: AgentFormData): AgentUpdate {
  // Build result object with ONLY the fields the backend expects
  const result: AgentUpdate = {
    name: String(data.name).trim(),
    model_ref_id: data.model_ref_id,
    max_iterations: data.max_iterations || 10,
  }
  
  // Add optional fields only if they have values
  if (data.description?.trim()) result.description = data.description.trim()
  if (data.system_message?.trim()) result.system_message = data.system_message.trim()
  if (data.temperature !== undefined && data.temperature !== null) result.temperature = data.temperature
  if (data.max_tokens !== undefined && data.max_tokens !== null) result.max_tokens = data.max_tokens
  if (data.tool_ids !== undefined) result.tool_ids = data.tool_ids

  return result
}

export default function EditAgentPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.id as string
  const queryClient = useQueryClient()
  const { setSelectedAgent } = useAgentStore()

  // Fetch agent data
  const { data: agent, isLoading: isLoadingAgent, error: agentError } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: async () => {
      const response = await agentsApi.get(agentId)
      return response.data
    },
    enabled: !!agentId,
  })

  const { data: connections, isLoading: isLoadingConnections } = useQuery({
    queryKey: ["connections"],
    queryFn: async () => {
      const res = await connectionsApi.list()
      return res.data as Connection[]
    },
  })

  const { data: modelRefs, isLoading: isLoadingModelRefs } = useQuery({
    queryKey: ["model-refs"],
    queryFn: async () => {
      const res = await modelRefsApi.list()
      return res.data as ModelRef[]
    },
  })

  const { data: toolsList = [], isLoading: isLoadingTools } = useToolsList()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: {
      name: "",
      description: "",
      system_message: "",
      max_iterations: 10,
      connection_id: "",
      model_ref_id: "",
      tool_ids: [],
    },
  })

  // Pre-populate form when agent data loads
  useEffect(() => {
    if (agent) {
      const connectionId = agent.model_ref?.connection?.id || ""
      const toolIds = agent.tools?.map((t) => t.id) ?? []
      reset({
        name: agent.name || "",
        description: agent.description || "",
        system_message: agent.system_message || "",
        max_iterations: agent.max_iterations || 10,
        temperature: agent.temperature,
        max_tokens: agent.max_tokens,
        connection_id: connectionId,
        model_ref_id: agent.model_ref_id || "",
        tool_ids: toolIds,
      })
    }
  }, [agent, reset])

  const selectedConnectionId = watch("connection_id")
  const selectedModelRefId = watch("model_ref_id")
  const selectedToolIds = watch("tool_ids") ?? []

  const connectionOptions = (connections || []).map((c) => ({
    value: c.id,
    label: c.name,
    description: `${c.connection_type} • ${c.provider}${c.base_url ? ` • ${c.base_url}` : ""}`,
  }))

  const filteredModelRefs = (modelRefs || []).filter((mr) =>
    selectedConnectionId ? mr.connection_id === selectedConnectionId : false
  )

  const modelRefOptions = filteredModelRefs.map((mr) => ({
    value: mr.id,
    label: mr.name,
    description: `runtime_id: ${mr.runtime_id}`,
  }))

  const updateAgentMutation = useMutation({
    mutationFn: async (apiData: AgentUpdate) => {
      const response = await agentsApi.update(agentId, apiData)
      return response.data
    },
    onSuccess: (updatedAgent) => {
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agentId] })
      
      // Update selected agent if it's the one being edited
      setSelectedAgent(updatedAgent)
      
      // Redirect to agents page
      router.push("/agents")
    },
    onError: (error: any) => {
      console.error("Failed to update agent:", error)
      // You can add toast notification here
    },
  })

  const onSubmit = async (data: AgentFormData) => {
    // Ensure transformation happens before sending
    const transformedData = transformFormDataToApi(data)
    await updateAgentMutation.mutateAsync(transformedData)
  }

  if (isLoadingAgent) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (agentError || !agent) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/agents">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Edit Agent</h1>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load agent. Please try again.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/agents">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Edit Agent</h1>
          <p className="text-muted-foreground">
            Update your AI agent configuration
          </p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Agent Details</CardTitle>
          <CardDescription>
            Update the information for your agent
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="connection_id">
                Connection <span className="text-destructive">*</span>
              </Label>
              <Combobox
                options={connectionOptions}
                value={selectedConnectionId}
                onValueChange={(value) => {
                  setValue("connection_id", value, { shouldValidate: true })
                  setValue("model_ref_id", "", { shouldValidate: true })
                }}
                placeholder={isLoadingConnections ? "Loading connections..." : "Select a connection..."}
                searchPlaceholder="Type to search connections..."
                emptyText="No connections found."
              />
              {errors.connection_id && (
                <p className="text-sm text-destructive">{errors.connection_id.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Pick where your model is hosted (vendor API or self-hosted endpoint)
              </p>
            </div>

            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="model_ref_id">
                Model <span className="text-destructive">*</span>
              </Label>
              <Combobox
                options={modelRefOptions}
                value={selectedModelRefId}
                onValueChange={(value) => setValue("model_ref_id", value, { shouldValidate: true })}
                placeholder={
                  !selectedConnectionId
                    ? "Select a connection first..."
                    : isLoadingModelRefs
                      ? "Loading models..."
                      : "Select a model..."
                }
                searchPlaceholder="Type to search models..."
                emptyText={selectedConnectionId ? "No models for this connection." : "Select a connection first."}
              />
              {errors.model_ref_id && (
                <p className="text-sm text-destructive">{errors.model_ref_id.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Choose the model reference to power this agent
              </p>
            </div>

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g., Customer Support Bot"
                {...register("name")}
                aria-invalid={errors.name ? "true" : "false"}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Brief description of what this agent does..."
                rows={3}
                {...register("description")}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description.message}</p>
              )}
            </div>

            {/* System Message */}
            <div className="space-y-2">
              <Label htmlFor="system_message">System Message</Label>
              <Textarea
                id="system_message"
                placeholder="Core instructions and behavior for the agent..."
                rows={5}
                {...register("system_message")}
              />
              <p className="text-xs text-muted-foreground">
                Define the agent&apos;s core behavior and instructions
              </p>
              {errors.system_message && (
                <p className="text-sm text-destructive">{errors.system_message.message}</p>
              )}
            </div>

            {/* Max Iterations */}
            <div className="space-y-2">
              <Label htmlFor="max_iterations">Max Iterations</Label>
              <Input
                id="max_iterations"
                type="number"
                min={1}
                max={50}
                placeholder="10"
                {...register("max_iterations", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Maximum number of tool-calling iterations (1-50)
              </p>
              {errors.max_iterations && (
                <p className="text-sm text-destructive">{errors.max_iterations.message}</p>
              )}
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <Label htmlFor="temperature">Temperature</Label>
              <Input
                id="temperature"
                type="number"
                step="0.1"
                min={0}
                max={2}
                placeholder="0.7"
                {...register("temperature", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Model temperature (0.0-2.0). Higher values make output more random.
              </p>
              {errors.temperature && (
                <p className="text-sm text-destructive">{errors.temperature.message}</p>
              )}
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <Label htmlFor="max_tokens">Max Tokens</Label>
              <Input
                id="max_tokens"
                type="number"
                min={1}
                placeholder="2048"
                {...register("max_tokens", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Maximum tokens in the response (optional)
              </p>
              {errors.max_tokens && (
                <p className="text-sm text-destructive">{errors.max_tokens.message}</p>
              )}
            </div>

            {/* Tools */}
            <div className="space-y-2">
              <Label>Tools</Label>
              <p className="text-xs text-muted-foreground">
                Attach tools this agent can use (e.g. RAG search). Create tools from the Tools page.
              </p>
              {isLoadingTools ? (
                <p className="text-sm text-muted-foreground">Loading tools...</p>
              ) : toolsList.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No tools yet. Create tools from the Tools page first.
                </p>
              ) : (
                <div className="rounded-md border p-3 space-y-2 max-h-[200px] overflow-auto">
                  {toolsList.map((tool) => (
                    <label
                      key={tool.id}
                      className="flex items-start gap-2 cursor-pointer hover:bg-muted/50 rounded p-2 -m-2"
                    >
                      <input
                        type="checkbox"
                        checked={selectedToolIds.includes(tool.id)}
                        onChange={() => {
                          const next = selectedToolIds.includes(tool.id)
                            ? selectedToolIds.filter((id) => id !== tool.id)
                            : [...selectedToolIds, tool.id]
                          setValue("tool_ids", next, { shouldValidate: true })
                        }}
                        className="mt-1 h-4 w-4 rounded border-input"
                      />
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-sm">{tool.name}</span>
                        <span className="text-xs text-muted-foreground ml-1 capitalize">
                          ({tool.tool_type})
                        </span>
                        {tool.description && (
                          <p className="text-xs text-muted-foreground mt-0.5 truncate">
                            {tool.description}
                          </p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || updateAgentMutation.isPending}>
              {isSubmitting || updateAgentMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                "Update Agent"
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
