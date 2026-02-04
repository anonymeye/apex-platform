"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Book, Trash2, Edit, FileText } from "lucide-react"
import type { KnowledgeBase } from "@/lib/types/knowledge"
import { useDeleteKnowledgeBase } from "@/lib/hooks/useKnowledge"
import { useState } from "react"

interface KnowledgeBaseCardProps {
  knowledgeBase: KnowledgeBase
  onSelect: (kb: KnowledgeBase) => void
  onEdit: (kb: KnowledgeBase) => void
  selectedId?: string | null
}

export function KnowledgeBaseCard({
  knowledgeBase,
  onSelect,
  onEdit,
  selectedId,
}: KnowledgeBaseCardProps) {
  const deleteMutation = useDeleteKnowledgeBase()
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm(`Are you sure you want to delete "${knowledgeBase.name}"? This will also delete all documents in this knowledge base.`)) {
      setIsDeleting(true)
      try {
        await deleteMutation.mutateAsync(knowledgeBase.id)
      } catch (error) {
        console.error("Failed to delete knowledge base:", error)
        alert("Failed to delete knowledge base. Please try again.")
      } finally {
        setIsDeleting(false)
      }
    }
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit(knowledgeBase)
  }

  const isSelected = selectedId === knowledgeBase.id

  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${
        isSelected ? "ring-2 ring-primary" : ""
      }`}
      onClick={() => onSelect(knowledgeBase)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Book className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{knowledgeBase.name}</CardTitle>
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEdit}
              className="h-8 w-8 p-0"
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {knowledgeBase.description && (
          <CardDescription>{knowledgeBase.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FileText className="h-4 w-4" />
          <span>Knowledge Base</span>
        </div>
      </CardContent>
    </Card>
  )
}
