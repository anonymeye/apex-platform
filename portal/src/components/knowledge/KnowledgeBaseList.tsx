"use client"

import { KnowledgeBaseCard } from "./KnowledgeBaseCard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Book, Plus, Loader2 } from "lucide-react"
import { useKnowledgeBases } from "@/lib/hooks/useKnowledge"
import type { KnowledgeBase } from "@/lib/types/knowledge"
import Link from "next/link"

interface KnowledgeBaseListProps {
  onSelect: (kb: KnowledgeBase) => void
  selectedId?: string | null
  onEdit: (kb: KnowledgeBase) => void
}

export function KnowledgeBaseList({
  onSelect,
  selectedId,
  onEdit,
}: KnowledgeBaseListProps) {
  const { data: knowledgeBases, isLoading, error } = useKnowledgeBases()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-destructive">
            Failed to load knowledge bases. Please try again.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!knowledgeBases || knowledgeBases.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <Book className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No knowledge bases yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first knowledge base to get started
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {knowledgeBases.map((kb) => (
        <KnowledgeBaseCard
          key={kb.id}
          knowledgeBase={kb}
          onSelect={onSelect}
          onEdit={onEdit}
          selectedId={selectedId}
        />
      ))}
    </div>
  )
}
