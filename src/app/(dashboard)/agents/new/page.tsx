"use client"

import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { agentsApi } from "@/lib/api/agents"
import { useAgentStore } from "@/lib/store/agentStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"

const agentSchema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name must be less than 100 characters"),
  description: z.string().optional(),
  system_message: z.string().optional(),
  persona: z.string().optional(),
  tone: z.string().optional(),
})

type AgentFormData = z.infer<typeof agentSchema>

export default function CreateAgentPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { setSelectedAgent } = useAgentStore()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: {
      name: "",
      description: "",
      system_message: "",
      persona: "",
      tone: "",
    },
  })

  const createAgentMutation = useMutation({
    mutationFn: async (data: AgentFormData) => {
      const response = await agentsApi.create(data)
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
    await createAgentMutation.mutateAsync(data)
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

            {/* Persona */}
            <div className="space-y-2">
              <Label htmlFor="persona">Persona</Label>
              <Input
                id="persona"
                placeholder="e.g., Friendly assistant, Professional consultant"
                {...register("persona")}
              />
              <p className="text-xs text-muted-foreground">
                Define the agent&apos;s personality or character
              </p>
              {errors.persona && (
                <p className="text-sm text-destructive">{errors.persona.message}</p>
              )}
            </div>

            {/* Tone */}
            <div className="space-y-2">
              <Label htmlFor="tone">Tone</Label>
              <Input
                id="tone"
                placeholder="e.g., Casual, Formal, Friendly"
                {...register("tone")}
              />
              <p className="text-xs text-muted-foreground">
                Define the communication style
              </p>
              {errors.tone && (
                <p className="text-sm text-destructive">{errors.tone.message}</p>
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
