"use client"

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Gavel, Loader2, Pencil, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { evaluationApi } from "@/lib/api/evaluation"
import { modelRefsApi } from "@/lib/api/model-refs"
import type { JudgeConfig, JudgeConfigCreate } from "@/lib/types/evaluation"
import type { ModelRef } from "@/lib/types/model"

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

function parseRubric(value: string): Record<string, unknown> | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  try {
    const parsed = JSON.parse(trimmed) as unknown
    if (parsed !== null && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>
    }
    return null
  } catch {
    return undefined
  }
}

interface JudgeConfigFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editing: JudgeConfig | null
  modelRefs: ModelRef[]
  onSuccess: () => void
}

function JudgeConfigForm({
  open,
  onOpenChange,
  editing,
  modelRefs,
  onSuccess,
}: JudgeConfigFormProps) {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const [promptTemplate, setPromptTemplate] = useState("")
  const [rubricText, setRubricText] = useState("")
  const [modelRefId, setModelRefId] = useState("")
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setFormError(null)
      if (editing) {
        setName(editing.name)
        setPromptTemplate(editing.prompt_template)
        setRubricText(
          editing.rubric != null ? JSON.stringify(editing.rubric, null, 2) : ""
        )
        setModelRefId(editing.model_ref_id)
      } else {
        setName("")
        setPromptTemplate("")
        setRubricText("")
        setModelRefId(modelRefs.length ? modelRefs[0].id : "")
      }
    }
  }, [open, editing, modelRefs])

  const createMutation = useMutation({
    mutationFn: async (data: JudgeConfigCreate) => {
      const res = await evaluationApi.createJudgeConfig(data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation-judge-configs"] })
      onSuccess()
      onOpenChange(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: JudgeConfigCreate }) => {
      const res = await evaluationApi.updateJudgeConfig(id, data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation-judge-configs"] })
      onSuccess()
      onOpenChange(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    const rubric = parseRubric(rubricText)
    if (rubricText.trim() && rubric === undefined) {
      setFormError("Rubric must be valid JSON (e.g. {\"accuracy\": \"1-5\"})")
      return
    }
    if (!name.trim()) {
      setFormError("Name is required")
      return
    }
    if (!modelRefId) {
      setFormError("Select a model")
      return
    }
    if (!promptTemplate.trim()) {
      setFormError("Prompt template is required")
      return
    }
    const payload: JudgeConfigCreate = {
      name: name.trim(),
      prompt_template: promptTemplate.trim(),
      rubric: rubric ?? undefined,
      model_ref_id: modelRefId,
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const error = formError ?? createMutation.error ?? updateMutation.error

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? "Edit judge config" : "Add judge config"}</DialogTitle>
          <DialogDescription>
            Define the LLM judge used for evaluation. Placeholders:{" "}
            <code className="text-xs bg-muted px-1 rounded">
              {"{{ user_message }}"}
            </code>
            ,{" "}
            <code className="text-xs bg-muted px-1 rounded">
              {"{{ agent_response }}"}
            </code>
            ,{" "}
            <code className="text-xs bg-muted px-1 rounded">
              {"{{ rubric }}"}
            </code>
            ,{" "}
            <code className="text-xs bg-muted px-1 rounded">
              {"{{ tool_calls }}"}
            </code>
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="judge-name">Name</Label>
            <Input
              id="judge-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. GPT-4o-mini accuracy"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="judge-model">Model</Label>
            <select
              id="judge-model"
              value={modelRefId}
              onChange={(e) => setModelRefId(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Select a model</option>
              {modelRefs.map((mr) => (
                <option key={mr.id} value={mr.id}>
                  {mr.name} ({mr.runtime_id})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="judge-prompt">Prompt template</Label>
            <Textarea
              id="judge-prompt"
              value={promptTemplate}
              onChange={(e) => setPromptTemplate(e.target.value)}
              placeholder="You are an impartial judge. Evaluate the following..."
              rows={6}
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="judge-rubric">Rubric (optional JSON)</Label>
            <Textarea
              id="judge-rubric"
              value={rubricText}
              onChange={(e) => setRubricText(e.target.value)}
              placeholder='{"accuracy": "1-5", "tone": "1-5"}'
              rows={3}
              className="font-mono text-sm"
            />
          </div>
          {error && (
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : String(error)}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {editing ? "Save" : "Create"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function JudgeConfigSection() {
  const queryClient = useQueryClient()
  const [formOpen, setFormOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<JudgeConfig | null>(null)

  const { data: judgeData, isLoading } = useQuery({
    queryKey: ["evaluation-judge-configs"],
    queryFn: async () => {
      const res = await evaluationApi.listJudgeConfigs({ skip: 0, limit: 100 })
      return res.data
    },
  })

  const { data: modelRefs = [] } = useQuery({
    queryKey: ["model-refs"],
    queryFn: async () => {
      const res = await modelRefsApi.list()
      return res.data as ModelRef[]
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await evaluationApi.deleteJudgeConfig(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evaluation-judge-configs"] })
    },
  })

  const configs = judgeData?.items ?? []
  const modelRefMap = Object.fromEntries((modelRefs as ModelRef[]).map((m) => [m.id, m]))

  const handleAdd = () => {
    setEditingConfig(null)
    setFormOpen(true)
  }

  const handleEdit = (config: JudgeConfig) => {
    setEditingConfig(config)
    setFormOpen(true)
  }

  const handleDelete = (config: JudgeConfig) => {
    if (!window.confirm(`Delete judge config "${config.name}"?`)) return
    deleteMutation.mutate(config.id)
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Gavel className="h-4 w-4" />
              Judge configs
            </CardTitle>
            <CardDescription>
              Reusable judge definitions (prompt, rubric, model) for evaluation runs
            </CardDescription>
          </div>
          <Button size="sm" onClick={handleAdd}>
            <Plus className="h-4 w-4 mr-1.5" />
            Add judge
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}
          {!isLoading && configs.length === 0 && (
            <p className="text-sm text-muted-foreground py-4">
              No judge configs yet. Add one to use when creating evaluation runs.
            </p>
          )}
          {!isLoading && configs.length > 0 && (
            <ul className="space-y-2">
              {configs.map((config) => (
                <li
                  key={config.id}
                  className="flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2 text-sm"
                >
                  <div>
                    <span className="font-medium">{config.name}</span>
                    <span className="text-muted-foreground ml-2">
                      {modelRefMap[config.model_ref_id]?.name ?? config.model_ref_id.slice(0, 8)}
                    </span>
                    <span className="text-muted-foreground text-xs ml-2">
                      {formatDate(config.created_at)}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleEdit(config)}
                      aria-label="Edit"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => handleDelete(config)}
                      disabled={deleteMutation.isPending}
                      aria-label="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <JudgeConfigForm
        open={formOpen}
        onOpenChange={setFormOpen}
        editing={editingConfig}
        modelRefs={modelRefs as ModelRef[]}
        onSuccess={() => setEditingConfig(null)}
      />
    </>
  )
}
