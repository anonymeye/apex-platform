"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus, X } from "lucide-react"
import { ToolList } from "@/components/tools/ToolList"
import { ToolForm } from "@/components/tools/ToolForm"
import type { Tool } from "@/lib/types/tools"

export default function ToolsPage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTool, setEditingTool] = useState<Tool | null>(null)

  const handleEdit = (tool: Tool) => {
    setEditingTool(tool)
    setShowCreateForm(false)
  }

  const handleCreateClick = () => {
    setShowCreateForm(true)
    setEditingTool(null)
  }

  const handleFormSuccess = () => {
    setShowCreateForm(false)
    setEditingTool(null)
  }

  const handleFormCancel = () => {
    setShowCreateForm(false)
    setEditingTool(null)
  }

  const showForm = showCreateForm || editingTool !== null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tools</h1>
          <p className="text-muted-foreground">
            Manage tools shared across your organization. Attach them to agents when creating or
            editing an agent.
          </p>
        </div>
        <Button onClick={handleCreateClick} disabled={showForm}>
          <Plus className="mr-2 h-4 w-4" />
          Create Tool
        </Button>
      </div>

      {showForm && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {editingTool ? "Edit Tool" : "Create Tool"}
            </h2>
            <Button variant="ghost" size="sm" onClick={handleFormCancel}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <ToolForm
            tool={editingTool}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        </div>
      )}

      {!showForm && <ToolList onEdit={handleEdit} />}
    </div>
  )
}
