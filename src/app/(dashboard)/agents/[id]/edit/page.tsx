"use client"

import { useRouter, useParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { agentsApi } from "@/lib/api/agents"
import { useAgentStore } from "@/lib/store/agentStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Combobox } from "@/components/ui/combobox"
import { OPEN_SOURCE_MODELS, getModelById, getModelIdFromBackendData } from "@/lib/constants/models"
import type { AgentUpdate } from "@/lib/types/agent"
import { useEffect } from "react"

const agentSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name must be less than 255 characters"),
  description: z.string().optional(),
  system_message: z.string().optional(),
  max_iterations: z.number().min(1).max(50).optional(),
  temperature: z.number().min(0).max(2).optional(),
  max_tokens: z.number().min(1).optional(),
  model_id: z.string().min(1, "Please select a model"),
})

type AgentFormData = z.infer<typeof agentSchema>

// Helper to convert model_id to backend format
function transformFormDataToApi(data: AgentFormData): AgentUpdate {
  if (!data.model_id) {
    throw new Error("Model ID is required")
  }
  
  const model = getModelById(data.model_id)
  if (!model) {
    throw new Error(`Invalid model selected: ${data.model_id}`)
  }

  // Normalize provider name to lowercase (backend expects lowercase provider names)
  const model_provider = model.provider.toLowerCase().replace(/\s+/g, "-")
  
  // Build result object with ONLY the fields the backend expects
  const result: AgentUpdate = {
    name: String(data.name).trim(),
    model_provider: model_provider,
    model_name: model.name,
    max_iterations: data.max_iterations || 10,
  }
  
  // Add optional fields only if they have values
  if (data.description?.trim()) result.description = data.description.trim()
  if (data.system_message?.trim()) result.system_message = data.system_message.trim()
  if (data.temperature !== undefined && data.temperature !== null) result.temperature = data.temperature
  if (data.max_tokens !== undefined && data.max_tokens !== null) result.max_tokens = data.max_tokens
  
  // Validate required fields
  if (!result.model_provider || !result.model_name) {
    throw new Error("Failed to extract model_provider and model_name from model_id")
  }
  
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
      model_id: "",
    },
  })

  // Pre-populate form when agent data loads
  useEffect(() => {
    if (agent) {
      const modelId = getModelIdFromBackendData(agent.model_provider, agent.model_name)
      
      reset({
        name: agent.name || "",
        description: agent.description || "",
        system_message: agent.system_message || "",
        max_iterations: agent.max_iterations || 10,
        temperature: agent.temperature,
        max_tokens: agent.max_tokens,
        model_id: modelId || "",
      })
    }
  }, [agent, reset])

  const selectedModelId = watch("model_id")

  const modelOptions = OPEN_SOURCE_MODELS.map((model) => ({
    value: model.id,
    label: model.name,
    description: `${model.provider} • ${model.size || "N/A"} • ${model.description}`,
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
              <Label htmlFor="model_id">
                LLM Model <span className="text-destructive">*</span>
              </Label>
              <Combobox
                options={modelOptions}
                value={selectedModelId}
                onValueChange={(value) => setValue("model_id", value, { shouldValidate: true })}
                placeholder="Search and select a model..."
                searchPlaceholder="Type to search models..."
                emptyText="No models found. Try a different search."
              />
              {errors.model_id && (
                <p className="text-sm text-destructive">{errors.model_id.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Choose the open source LLM model to power this agent
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
