"use client"

import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { agentsApi } from "@/lib/api/agents"
import { connectionsApi } from "@/lib/api/connections"
import { modelRefsApi } from "@/lib/api/model-refs"
import { useAgentStore } from "@/lib/store/agentStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Combobox } from "@/components/ui/combobox"
import type { AgentCreate } from "@/lib/types/agent"
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
})

type AgentFormData = z.infer<typeof agentSchema>

function transformFormDataToApi(data: AgentFormData): AgentCreate {
  if (!data.model_ref_id) {
    throw new Error("ModelRef ID is required")
  }

  const result: AgentCreate = {
    name: String(data.name).trim(),
    model_ref_id: data.model_ref_id,
    max_iterations: data.max_iterations || 10,
    config: {},
  }
  
  // Add optional fields only if they have values
  if (data.description?.trim()) result.description = data.description.trim()
  if (data.system_message?.trim()) result.system_message = data.system_message.trim()
  if (data.temperature !== undefined && data.temperature !== null) result.temperature = data.temperature
  if (data.max_tokens !== undefined && data.max_tokens !== null) result.max_tokens = data.max_tokens
  
  return result
}

export default function CreateAgentPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { setSelectedAgent } = useAgentStore()

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

  const {
    register,
    handleSubmit,
    watch,
    setValue,
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
    },
  })

  const selectedConnectionId = watch("connection_id")
  const selectedModelRefId = watch("model_ref_id")

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

  const createAgentMutation = useMutation({
    mutationFn: async (apiData: AgentCreate) => {
      // Data is already transformed in onSubmit
      const response = await agentsApi.create(apiData)
      return response.data
    },
    onSuccess: (agent) => {
      // Invalidate agents list to refetch
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      
      // Auto-select the newly created agent
      setSelectedAgent(agent)
      
      // Redirect to agents page
      router.push("/agents")
    },
    onError: (error: any) => {
      console.error("Failed to create agent:", error)
      // You can add toast notification here
    },
  })

  const onSubmit = async (data: AgentFormData) => {
    // Ensure transformation happens before sending
    const transformedData = transformFormDataToApi(data)
    await createAgentMutation.mutateAsync(transformedData as any)
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
          <h1 className="text-3xl font-bold">Create Agent</h1>
          <p className="text-muted-foreground">
            Create a new AI agent with custom configuration
          </p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Agent Details</CardTitle>
          <CardDescription>
            Fill in the information to create your new agent
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
                  // Reset model selection when connection changes
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
          </CardContent>
          <CardFooter className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || createAgentMutation.isPending}>
              {isSubmitting || createAgentMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Agent"
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
