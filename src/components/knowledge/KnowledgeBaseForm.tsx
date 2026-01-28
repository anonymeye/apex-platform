"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCreateKnowledgeBase, useUpdateKnowledgeBase } from "@/lib/hooks/useKnowledge"
import type { KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate } from "@/lib/types/knowledge"
import { Loader2 } from "lucide-react"

interface KnowledgeBaseFormProps {
  knowledgeBase?: KnowledgeBase | null
  onSuccess?: () => void
  onCancel?: () => void
}

export function KnowledgeBaseForm({
  knowledgeBase,
  onSuccess,
  onCancel,
}: KnowledgeBaseFormProps) {
  const createMutation = useCreateKnowledgeBase()
  const updateMutation = useUpdateKnowledgeBase()

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  useEffect(() => {
    if (knowledgeBase) {
      setName(knowledgeBase.name)
      setDescription(knowledgeBase.description || "")
    } else {
      setName("")
      setDescription("")
    }
  }, [knowledgeBase])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const isEditing = !!knowledgeBase
    const isLoading = isEditing ? updateMutation.isPending : createMutation.isPending

    if (isLoading) return

    try {
      if (isEditing) {
        const updateData: KnowledgeBaseUpdate = {}
        if (name !== knowledgeBase.name) updateData.name = name
        if (description !== (knowledgeBase.description || "")) {
          updateData.description = description || null
        }

        if (Object.keys(updateData).length > 0) {
          await updateMutation.mutateAsync({
            id: knowledgeBase.id,
            data: updateData,
          })
        }
      } else {
        const createData: KnowledgeBaseCreate = {
          name,
          description: description || null,
        }
        await createMutation.mutateAsync(createData)
      }

      onSuccess?.()
    } catch (error) {
      console.error("Failed to save knowledge base:", error)
      alert("Failed to save knowledge base. Please try again.")
    }
  }

  const isLoading = knowledgeBase
    ? updateMutation.isPending
    : createMutation.isPending

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {knowledgeBase ? "Edit Knowledge Base" : "Create Knowledge Base"}
        </CardTitle>
        <CardDescription>
          {knowledgeBase
            ? "Update the knowledge base details"
            : "Create a new knowledge base to organize your documents"}
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
              placeholder="e.g., Product Documentation"
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description for this knowledge base"
              rows={3}
              disabled={isLoading}
            />
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
            <Button type="submit" disabled={isLoading || !name.trim()}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {knowledgeBase ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
