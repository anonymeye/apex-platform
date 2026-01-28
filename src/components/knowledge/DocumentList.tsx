"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Trash2, Loader2 } from "lucide-react"
import { useDocuments, useDeleteDocument } from "@/lib/hooks/useKnowledge"
import type { Document } from "@/lib/types/knowledge"
import { useState } from "react"

interface DocumentListProps {
  kbId: string
}

export function DocumentList({ kbId }: DocumentListProps) {
  const { data: documents, isLoading, error } = useDocuments(kbId)
  const deleteMutation = useDeleteDocument()
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())

  const handleDelete = async (doc: Document) => {
    if (confirm(`Are you sure you want to delete this document?`)) {
      setDeletingIds((prev) => new Set(prev).add(doc.id))
      try {
        await deleteMutation.mutateAsync({
          kbId,
          docId: doc.id,
        })
      } catch (error) {
        console.error("Failed to delete document:", error)
        alert("Failed to delete document. Please try again.")
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev)
          next.delete(doc.id)
          return next
        })
      }
    }
  }

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
            Failed to load documents. Please try again.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!documents || documents.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No documents yet</h3>
            <p className="text-muted-foreground">
              Upload documents to add them to this knowledge base
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Documents ({documents.length})</CardTitle>
          <CardDescription>
            Documents in this knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {documents.map((doc) => {
              const isDeleting = deletingIds.has(doc.id)
              return (
                <div
                  key={doc.id}
                  className="flex items-start justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-medium truncate">
                        {doc.source || `Document ${doc.chunk_index !== null ? `(Chunk ${doc.chunk_index})` : doc.id.slice(0, 8)}`}
                      </span>
                      {doc.chunk_index !== null && (
                        <span className="text-xs text-muted-foreground">
                          Chunk {doc.chunk_index}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {doc.content}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(doc)}
                    disabled={isDeleting}
                    className="ml-2 h-8 w-8 p-0 text-destructive hover:text-destructive flex-shrink-0"
                  >
                    {isDeleting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
