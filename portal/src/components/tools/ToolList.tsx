"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Wrench, Trash2, Edit, Loader2 } from "lucide-react"
import { useToolsList, useDeleteTool } from "@/lib/hooks/useTools"
import type { Tool } from "@/lib/types/tools"
import { useState } from "react"

interface ToolListProps {
  onEdit?: (tool: Tool) => void
}

export function ToolList({ onEdit }: ToolListProps) {
  const { data: tools, isLoading, error } = useToolsList()
  const deleteMutation = useDeleteTool()
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())

  const handleDelete = async (tool: Tool) => {
    if (
      confirm(
        `Are you sure you want to delete the tool "${tool.name}"? This will remove it from all agents that use it.`
      )
    ) {
      setDeletingIds((prev) => new Set(prev).add(tool.id))
      try {
        await deleteMutation.mutateAsync(tool.id)
      } catch (err) {
        console.error("Failed to delete tool:", err)
        alert("Failed to delete tool. Please try again.")
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev)
          next.delete(tool.id)
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
          <p className="text-destructive">Failed to load tools. Please try again.</p>
        </CardContent>
      </Card>
    )
  }

  if (!tools || tools.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <Wrench className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No tools yet</h3>
            <p className="text-muted-foreground">
              Create a tool to make it available to all agents, or upload documents to a knowledge
              base to auto-create RAG tools.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tools ({tools.length})</CardTitle>
        <CardDescription>
          Tools shared across your organization. Attach them to agents when creating or editing an
          agent.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tools.map((tool) => {
            const isDeleting = deletingIds.has(tool.id)
            return (
              <div
                key={tool.id}
                className="flex items-start justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Wrench className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="font-medium">{tool.name}</span>
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded capitalize">
                      {tool.tool_type}
                    </span>
                    {tool.knowledge_base_id && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                        Linked to KB
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{tool.description}</p>
                </div>
                <div className="flex gap-1 ml-4">
                  {onEdit && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(tool)}
                      className="h-8 w-8 p-0"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(tool)}
                    disabled={isDeleting}
                    className="h-8 w-8 p-0 text-destructive hover:text-destructive"
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
      </CardContent>
    </Card>
  )
}
