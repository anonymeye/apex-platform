"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FileText, Trash2, Loader2, Search, Eye, CheckSquare, Square } from "lucide-react"
import { useDocuments, useDeleteDocument, useBulkDeleteDocuments } from "@/lib/hooks/useKnowledge"
import type { Document } from "@/lib/types/knowledge"
import { useState, useMemo } from "react"

interface DocumentListProps {
  kbId: string
  onPreview?: (doc: Document) => void
}

export function DocumentList({ kbId, onPreview }: DocumentListProps) {
  const { data: documents, isLoading, error } = useDocuments(kbId)
  const deleteMutation = useDeleteDocument()
  const bulkDeleteMutation = useBulkDeleteDocuments()
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedSource, setSelectedSource] = useState<string>("all")

  // Filter documents
  const filteredDocuments = useMemo(() => {
    if (!documents) return []

    let filtered = documents

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (doc) =>
          doc.content.toLowerCase().includes(query) ||
          doc.source?.toLowerCase().includes(query) ||
          JSON.stringify(doc.metadata || {}).toLowerCase().includes(query)
      )
    }

    // Filter by source
    if (selectedSource !== "all") {
      filtered = filtered.filter((doc) => doc.source === selectedSource)
    }

    return filtered
  }, [documents, searchQuery, selectedSource])

  // Get unique sources for filter
  const sources = useMemo(() => {
    if (!documents) return []
    const uniqueSources = new Set(documents.map((doc) => doc.source).filter(Boolean))
    return Array.from(uniqueSources).sort()
  }, [documents])

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

  const handleToggleSelect = (docId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(docId)) {
        next.delete(docId)
      } else {
        next.add(docId)
      }
      return next
    })
  }

  const handleSelectAll = () => {
    if (selectedIds.size === filteredDocuments.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredDocuments.map((doc) => doc.id)))
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return

    if (confirm(`Are you sure you want to delete ${selectedIds.size} document(s)?`)) {
      const idsToDelete = Array.from(selectedIds)
      setDeletingIds((prev) => new Set([...prev, ...idsToDelete]))
      try {
        await bulkDeleteMutation.mutateAsync({
          kbId,
          documentIds: idsToDelete,
        })
        setSelectedIds(new Set())
      } catch (error) {
        console.error("Failed to delete documents:", error)
        alert("Failed to delete documents. Please try again.")
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev)
          idsToDelete.forEach((id) => next.delete(id))
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
            {filteredDocuments.length !== documents.length
              ? `Showing ${filteredDocuments.length} of ${documents.length} documents`
              : "Documents in this knowledge base"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Search and Filter */}
            <div className="space-y-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="flex items-center justify-between">
                {sources.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant={selectedSource === "all" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedSource("all")}
                    >
                      All
                    </Button>
                    {sources.map((source) => (
                      <Button
                        key={source}
                        variant={selectedSource === source ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedSource(source)}
                      >
                        {source}
                      </Button>
                    ))}
                  </div>
                )}
                {selectedIds.size > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {selectedIds.size} selected
                    </span>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleBulkDelete}
                      disabled={bulkDeleteMutation.isPending}
                    >
                      {bulkDeleteMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Trash2 className="h-4 w-4 mr-1" />
                          Delete Selected
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Documents List */}
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {searchQuery || selectedSource !== "all"
                  ? "No documents match your filters"
                  : "No documents yet"}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredDocuments.length > 0 && (
                  <div className="flex items-center gap-2 pb-2 border-b">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleSelectAll}
                      className="h-8"
                    >
                      {selectedIds.size === filteredDocuments.length ? (
                        <CheckSquare className="h-4 w-4" />
                      ) : (
                        <Square className="h-4 w-4" />
                      )}
                      <span className="ml-2">
                        {selectedIds.size === filteredDocuments.length
                          ? "Deselect All"
                          : "Select All"}
                      </span>
                    </Button>
                  </div>
                )}
                {filteredDocuments.map((doc) => {
                  const isDeleting = deletingIds.has(doc.id)
                  const isSelected = selectedIds.has(doc.id)
                  return (
                    <div
                      key={doc.id}
                      className={`flex items-start gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors ${
                        isSelected ? "bg-primary/5 border-primary" : ""
                      }`}
                    >
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleSelect(doc.id)}
                        className="h-6 w-6 p-0 mt-0.5 flex-shrink-0"
                      >
                        {isSelected ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <Square className="h-4 w-4" />
                        )}
                      </Button>
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
                      <div className="flex gap-1 ml-2">
                        {onPreview && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onPreview(doc)}
                            className="h-8 w-8 p-0 flex-shrink-0"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(doc)}
                          disabled={isDeleting}
                          className="h-8 w-8 p-0 text-destructive hover:text-destructive flex-shrink-0"
                        >
                          {isDeleting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
