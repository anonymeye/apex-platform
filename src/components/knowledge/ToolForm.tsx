"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useUpdateTool } from "@/lib/hooks/useKnowledge"
import type { Tool, ToolUpdate } from "@/lib/types/knowledge"
import { Loader2 } from "lucide-react"

interface ToolFormProps {
  tool: Tool
  kbId: string
  onSuccess?: () => void
  onCancel?: () => void
}

export function ToolForm({ tool, kbId, onSuccess, onCancel }: ToolFormProps) {
  const updateMutation = useUpdateTool()

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [ragK, setRagK] = useState<number>(5)
  const [ragTemplate, setRagTemplate] = useState("")

  useEffect(() => {
    if (tool) {
      setName(tool.name)
      setDescription(tool.description)
      setRagK(tool.rag_k || 5)
      setRagTemplate(tool.rag_template || "")
    }
  }, [tool])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const updateData: ToolUpdate = {}
    if (name !== tool.name) updateData.name = name
    if (description !== tool.description) updateData.description = description
    if (ragK !== (tool.rag_k || 5)) updateData.rag_k = ragK
    if (ragTemplate !== (tool.rag_template || "")) {
      updateData.rag_template = ragTemplate || null
    }

    if (Object.keys(updateData).length === 0) {
      onSuccess?.()
      return
    }

    try {
      await updateMutation.mutateAsync({
        kbId,
        toolId: tool.id,
        data: updateData,
      })
      onSuccess?.()
    } catch (error) {
      console.error("Failed to update tool:", error)
      alert("Failed to update tool. Please try again.")
    }
  }

  const isLoading = updateMutation.isPending

  return (
    <Card>
      <CardHeader>
        <CardTitle>Edit Tool</CardTitle>
        <CardDescription>
          Customize the tool name, description, and RAG parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Tool Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., search_product_docs"
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tool description that agents will see"
              rows={3}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="rag-k">Number of Chunks to Retrieve (k)</Label>
            <Input
              id="rag-k"
              type="number"
              value={ragK}
              onChange={(e) => setRagK(parseInt(e.target.value) || 5)}
              min={1}
              max={20}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Number of document chunks to retrieve when searching (1-20)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="rag-template">RAG Template (Optional)</Label>
            <Textarea
              id="rag-template"
              value={ragTemplate}
              onChange={(e) => setRagTemplate(e.target.value)}
              placeholder="Custom RAG prompt template. Leave empty for default."
              rows={6}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Custom prompt template for RAG. Use {"{context}"} for retrieved documents and {"{query}"} for the user query.
            </p>
          </div>

          <div className="flex gap-2 justify-end">
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isLoading}
              >
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={isLoading || !name.trim() || !description.trim()}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Update Tool
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
