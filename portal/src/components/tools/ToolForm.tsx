"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCreateTool, useUpdateTool } from "@/lib/hooks/useTools"
import type { Tool, ToolCreate, ToolUpdate } from "@/lib/types/tools"
import { Loader2 } from "lucide-react"

const TOOL_TYPES = [
  { value: "rag", label: "RAG (retrieval)" },
  { value: "api", label: "API" },
  { value: "function", label: "Function" },
] as const

interface ToolFormProps {
  tool?: Tool | null
  onSuccess?: () => void
  onCancel?: () => void
}

export function ToolForm({ tool, onSuccess, onCancel }: ToolFormProps) {
  const isEditing = !!tool

  const createMutation = useCreateTool()
  const updateMutation = useUpdateTool()

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [toolType, setToolType] = useState<string>("rag")
  const [configJson, setConfigJson] = useState("")

  useEffect(() => {
    if (tool) {
      setName(tool.name)
      setDescription(tool.description)
      setToolType(tool.tool_type)
      setConfigJson(
        tool.config && Object.keys(tool.config).length > 0
          ? JSON.stringify(tool.config, null, 2)
          : ""
      )
    } else {
      setName("")
      setDescription("")
      setToolType("rag")
      setConfigJson("")
    }
  }, [tool])

  const parseConfig = (): Record<string, unknown> | undefined => {
    const trimmed = configJson.trim()
    if (!trimmed) return undefined
    try {
      return JSON.parse(trimmed) as Record<string, unknown>
    } catch {
      return undefined
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const config = parseConfig()
    if (configJson.trim() && config === undefined) {
      alert("Invalid JSON in config. Fix the syntax or clear the field.")
      return
    }

    if (isEditing && tool) {
      const updateData: ToolUpdate = {}
      if (name !== tool.name) updateData.name = name
      if (description !== tool.description) updateData.description = description
      if (config !== undefined) updateData.config = config

      if (Object.keys(updateData).length === 0) {
        onSuccess?.()
        return
      }

      try {
        await updateMutation.mutateAsync({ id: tool.id, data: updateData })
        onSuccess?.()
      } catch (err) {
        console.error("Failed to update tool:", err)
        alert("Failed to update tool. Please try again.")
      }
    } else {
      const createData: ToolCreate = {
        name: name.trim(),
        description: description.trim(),
        tool_type: toolType,
      }
      if (config) createData.config = config

      try {
        await createMutation.mutateAsync(createData)
        onSuccess?.()
      } catch (err) {
        console.error("Failed to create tool:", err)
        alert("Failed to create tool. Please try again.")
      }
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditing ? "Edit Tool" : "Create Tool"}</CardTitle>
        <CardDescription>
          {isEditing
            ? "Update the tool name, description, or config."
            : "Add a new tool that agents can use. RAG tools are often auto-created from knowledge bases."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. search_product_docs"
              required
              disabled={isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description that agents will see when choosing to use this tool"
              rows={3}
              required
              disabled={isPending}
            />
          </div>

          {!isEditing && (
            <div className="space-y-2">
              <Label htmlFor="tool_type">Type</Label>
              <select
                id="tool_type"
                value={toolType}
                onChange={(e) => setToolType(e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                disabled={isPending}
              >
                {TOOL_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="config">Config (optional JSON)</Label>
            <Textarea
              id="config"
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              placeholder='{"rag_k": 5, "rag_template": "..."}'
              rows={4}
              className="font-mono text-sm"
              disabled={isPending}
            />
            <p className="text-xs text-muted-foreground">
              Type-specific options. For RAG: rag_k, rag_template, etc.
            </p>
          </div>

          <div className="flex gap-2 justify-end">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              disabled={isPending || !name.trim() || !description.trim()}
            >
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEditing ? "Update Tool" : "Create Tool"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
