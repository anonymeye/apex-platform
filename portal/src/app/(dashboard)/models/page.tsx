"use client"

import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Database, Loader2, Trash2 } from "lucide-react"

import { modelRefsApi } from "@/lib/api/model-refs"
import { connectionsApi } from "@/lib/api/connections"
import type { Connection, ModelRef, ModelRefCreate } from "@/lib/types/model"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Combobox } from "@/components/ui/combobox"

const schema = z.object({
  connection_id: z.string().min(1, "Select a connection"),
  name: z.string().min(1, "Name is required"),
  runtime_id: z.string().min(1, "runtime_id is required"),
})

type FormData = z.infer<typeof schema>

export default function ModelsPage() {
  const queryClient = useQueryClient()

  const { data: connections } = useQuery({
    queryKey: ["connections"],
    queryFn: async () => {
      const res = await connectionsApi.list()
      return res.data as Connection[]
    },
  })

  const { data: modelRefs, isLoading } = useQuery({
    queryKey: ["model-refs"],
    queryFn: async () => {
      const res = await modelRefsApi.list()
      return res.data as ModelRef[]
    },
  })

  const createMutation = useMutation({
    mutationFn: async (payload: ModelRefCreate) => {
      const res = await modelRefsApi.create(payload)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["model-refs"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await modelRefsApi.delete(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["model-refs"] })
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      connection_id: "",
      name: "",
      runtime_id: "",
    },
  })

  const connectionOptions = (connections || []).map((c) => ({
    value: c.id,
    label: c.name,
    description: `${c.connection_type} • ${c.provider}`,
  }))

  const selectedConnectionId = watch("connection_id")

  const onSubmit = async (data: FormData) => {
    await createMutation.mutateAsync({
      connection_id: data.connection_id,
      name: data.name.trim(),
      runtime_id: data.runtime_id.trim(),
      config: {},
    })
    reset()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Database className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Models</h1>
          <p className="text-muted-foreground">Create ModelRefs (model choices) under a Connection</p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Create Model</CardTitle>
          <CardDescription>
            A ModelRef is a stable pointer to a model identifier on a specific connection
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Connection</Label>
              <Combobox
                options={connectionOptions}
                value={selectedConnectionId}
                onValueChange={(v) => setValue("connection_id", v, { shouldValidate: true })}
                placeholder="Select connection..."
                emptyText="No connections found. Create one first."
              />
              {errors.connection_id && (
                <p className="text-sm text-destructive">{errors.connection_id.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="e.g., GPT-4o Mini" {...register("name")} />
              {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="runtime_id">runtime_id</Label>
              <Input id="runtime_id" placeholder='e.g., "gpt-4o-mini" or "llama-3.3-70b-versatile"' {...register("runtime_id")} />
              {errors.runtime_id && <p className="text-sm text-destructive">{errors.runtime_id.message}</p>}
              <p className="text-xs text-muted-foreground">
                This is the identifier your runtime expects (vendor model id or self-hosted model name).
              </p>
            </div>

            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Model"
              )}
            </Button>
          </CardContent>
        </form>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing Models</CardTitle>
          <CardDescription>Agents pin to these via model_ref_id</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading...
            </div>
          )}
          {!isLoading && (!modelRefs || modelRefs.length === 0) && (
            <p className="text-sm text-muted-foreground">No models yet.</p>
          )}
          {modelRefs?.map((mr) => (
            <div key={mr.id} className="flex items-center justify-between rounded-md border p-3">
              <div className="space-y-1">
                <div className="font-medium">{mr.name}</div>
                <div className="text-sm text-muted-foreground">
                  {mr.connection?.name ? `${mr.connection.name} • ` : ""}
                  runtime_id: {mr.runtime_id}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteMutation.mutate(mr.id)}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

