"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plug, Loader2, Trash2, Pencil, X } from "lucide-react"

import { connectionsApi } from "@/lib/api/connections"
import type { Connection, ConnectionCreate } from "@/lib/types/model"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Combobox } from "@/components/ui/combobox"

const schema = z.object({
  name: z.string().min(1),
  connection_type: z.enum(["vendor_api", "openai_compatible"]),
  provider: z.enum(["openai", "anthropic", "groq", "openai_compatible"]),
  base_url: z.string().optional(),
  auth_type: z.enum(["env", "none"]),
  api_key_env_var: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export default function ConnectionsPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data: connections, isLoading } = useQuery({
    queryKey: ["connections"],
    queryFn: async () => {
      const res = await connectionsApi.list()
      return res.data as Connection[]
    },
  })

  const createMutation = useMutation({
    mutationFn: async (payload: ConnectionCreate) => {
      const res = await connectionsApi.create(payload)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<ConnectionCreate> }) => {
      const res = await connectionsApi.update(id, payload)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
      queryClient.invalidateQueries({ queryKey: ["model-refs"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await connectionsApi.delete(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
      queryClient.invalidateQueries({ queryKey: ["model-refs"] })
    },
  })

  const normalizeAuthType = (authType: string | null | undefined): "env" | "none" => {
    const v = (authType || "").toLowerCase()
    return v === "none" ? "none" : "env"
  }

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
      connection_type: "vendor_api",
      provider: "openai",
      auth_type: "env",
    },
  })

  const onSubmit = async (data: FormData) => {
    await createMutation.mutateAsync({
      name: data.name.trim(),
      connection_type: data.connection_type,
      provider: data.provider,
      base_url: data.base_url?.trim() || undefined,
      auth_type: data.auth_type,
      api_key_env_var: data.api_key_env_var?.trim() || undefined,
      config: {},
    })
    reset()
  }

  const connectionType = watch("connection_type")
  const authType = watch("auth_type")

  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    watch: watchEdit,
    setValue: setValueEdit,
    reset: resetEdit,
    formState: { errors: editErrors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      connection_type: "vendor_api",
      provider: "openai",
      auth_type: "env",
    },
  })

  const editConnectionType = watchEdit("connection_type")
  const editAuthType = watchEdit("auth_type")

  const beginEdit = (c: Connection) => {
    setEditingId(c.id)
    resetEdit({
      name: c.name,
      connection_type: (c.connection_type as any) || "vendor_api",
      provider: (c.provider as any) || "openai",
      base_url: c.base_url || undefined,
      auth_type: normalizeAuthType(c.auth_type),
      api_key_env_var: c.api_key_env_var || undefined,
    })
  }

  const cancelEdit = () => {
    setEditingId(null)
    resetEdit({
      connection_type: "vendor_api",
      provider: "openai",
      auth_type: "env",
    })
  }

  const onSubmitEdit = async (data: FormData) => {
    if (!editingId) return
    await updateMutation.mutateAsync({
      id: editingId,
      payload: {
        name: data.name.trim(),
        connection_type: data.connection_type,
        provider: data.provider,
        base_url: data.base_url?.trim() || undefined,
        auth_type: data.auth_type,
        api_key_env_var: data.api_key_env_var?.trim() || undefined,
        config: {},
      },
    })
    cancelEdit()
  }

  const connectionTypeOptions = [
    { value: "vendor_api", label: "Vendor API", description: "OpenAI/Anthropic/Groq via their hosted APIs" },
    { value: "openai_compatible", label: "OpenAI-compatible", description: "Self-hosted endpoint (vLLM/TGI/etc.)" },
  ]

  const providerOptions = [
    { value: "openai", label: "OpenAI", description: "OpenAI API" },
    { value: "anthropic", label: "Anthropic", description: "Anthropic Claude API" },
    { value: "groq", label: "Groq", description: "Groq OpenAI-compatible API" },
    { value: "openai_compatible", label: "OpenAI-compatible", description: "Self-hosted OpenAI-compatible endpoint" },
  ]

  const authTypeOptions = [
    { value: "env", label: "Environment variable", description: "Read API key from server env var" },
    { value: "none", label: "No auth", description: "Do not send Authorization header" },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Plug className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Connections</h1>
          <p className="text-muted-foreground">Configure vendor APIs or self-hosted endpoints</p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Create Connection</CardTitle>
          <CardDescription>Define where models are hosted and how to call them</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" placeholder="e.g., OpenAI Prod" {...register("name")} />
              {errors.name && <p className="text-sm text-destructive">Name is required</p>}
            </div>

            <div className="space-y-2">
              <Label>Connection Type</Label>
              <Combobox
                options={connectionTypeOptions}
                value={connectionType}
                onValueChange={(v) => setValue("connection_type", v as any, { shouldValidate: true })}
                placeholder="Select connection type..."
              />
            </div>

            <div className="space-y-2">
              <Label>Provider</Label>
              <Combobox
                options={providerOptions}
                value={watch("provider")}
                onValueChange={(v) => setValue("provider", v as any, { shouldValidate: true })}
                placeholder="Select provider..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="base_url">Base URL (optional)</Label>
              <Input
                id="base_url"
                placeholder={connectionType === "openai_compatible" ? "http://localhost:8000/v1" : "Leave empty for default"}
                {...register("base_url")}
              />
              {connectionType === "openai_compatible" && (
                <p className="text-xs text-muted-foreground">Required for OpenAI-compatible connections.</p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Auth</Label>
              <Combobox
                options={authTypeOptions}
                value={authType}
                onValueChange={(v) => setValue("auth_type", v as any, { shouldValidate: true })}
                placeholder="Select auth type..."
              />
            </div>

            {authType === "env" && (
              <div className="space-y-2">
                <Label htmlFor="api_key_env_var">API Key Env Var (optional)</Label>
                <Input id="api_key_env_var" placeholder="e.g., OPENAI_API_KEY" {...register("api_key_env_var")} />
                <p className="text-xs text-muted-foreground">
                  If empty, backend uses provider defaults (OPENAI_API_KEY / ANTHROPIC_API_KEY / GROQ_API_KEY).
                </p>
              </div>
            )}

            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Connection"
              )}
            </Button>
          </CardContent>
        </form>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing Connections</CardTitle>
          <CardDescription>Used by Model Refs (and then by Agents)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {editingId && (
            <Card className="border-primary/40">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">Edit Connection</CardTitle>
                    <CardDescription>
                      Update metadata. API keys should be provided via server env vars.
                    </CardDescription>
                  </div>
                  <Button variant="ghost" size="icon" onClick={cancelEdit}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <form onSubmit={handleSubmitEdit(onSubmitEdit)}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit_name">Name</Label>
                    <Input id="edit_name" {...registerEdit("name")} />
                    {editErrors.name && <p className="text-sm text-destructive">Name is required</p>}
                  </div>

                  <div className="space-y-2">
                    <Label>Connection Type</Label>
                    <Combobox
                      options={connectionTypeOptions}
                      value={editConnectionType}
                      onValueChange={(v) => setValueEdit("connection_type", v as any, { shouldValidate: true })}
                      placeholder="Select connection type..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <Combobox
                      options={providerOptions}
                      value={watchEdit("provider")}
                      onValueChange={(v) => setValueEdit("provider", v as any, { shouldValidate: true })}
                      placeholder="Select provider..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit_base_url">Base URL (optional)</Label>
                    <Input
                      id="edit_base_url"
                      placeholder={editConnectionType === "openai_compatible" ? "http://localhost:8000/v1" : "Leave empty for default"}
                      {...registerEdit("base_url")}
                    />
                    {editConnectionType === "openai_compatible" && (
                      <p className="text-xs text-muted-foreground">Required for OpenAI-compatible connections.</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Auth</Label>
                    <Combobox
                      options={authTypeOptions}
                      value={editAuthType}
                      onValueChange={(v) => setValueEdit("auth_type", v as any, { shouldValidate: true })}
                      placeholder="Select auth type..."
                    />
                  </div>

                  {editAuthType === "env" && (
                    <div className="space-y-2">
                      <Label htmlFor="edit_api_key_env_var">API Key Env Var (optional)</Label>
                      <Input id="edit_api_key_env_var" placeholder="e.g., GROQ_API_KEY" {...registerEdit("api_key_env_var")} />
                      <p className="text-xs text-muted-foreground">
                        This is the <span className="font-medium">env var name</span> on the backend container, not the key itself.
                      </p>
                    </div>
                  )}

                  <div className="flex items-center justify-end gap-2">
                    <Button type="button" variant="outline" onClick={cancelEdit} disabled={updateMutation.isPending}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={updateMutation.isPending}>
                      {updateMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        "Save changes"
                      )}
                    </Button>
                  </div>
                </CardContent>
              </form>
            </Card>
          )}

          {isLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading...
            </div>
          )}
          {!isLoading && (!connections || connections.length === 0) && (
            <p className="text-sm text-muted-foreground">No connections yet.</p>
          )}
          {connections?.map((c) => (
            <div key={c.id} className="flex items-center justify-between rounded-md border p-3">
              <div className="space-y-1">
                <div className="font-medium">{c.name}</div>
                <div className="text-sm text-muted-foreground">
                  {c.connection_type} • {c.provider}
                  {c.base_url ? ` • ${c.base_url}` : ""}
                </div>
                {c.auth_type?.toLowerCase() !== "none" && (
                  <div className="text-xs text-muted-foreground">
                    Auth: env var {c.api_key_env_var || "(default for provider)"}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => beginEdit(c)}
                  disabled={deleteMutation.isPending || updateMutation.isPending}
                  aria-label="Edit connection"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => deleteMutation.mutate(c.id)}
                  disabled={deleteMutation.isPending || updateMutation.isPending}
                  aria-label="Delete connection"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

