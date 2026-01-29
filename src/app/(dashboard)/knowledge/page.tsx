"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus, X, ArrowLeft } from "lucide-react"
import { KnowledgeBaseList } from "@/components/knowledge/KnowledgeBaseList"
import { KnowledgeBaseForm } from "@/components/knowledge/KnowledgeBaseForm"
import { DocumentList } from "@/components/knowledge/DocumentList"
import { DocumentUpload } from "@/components/knowledge/DocumentUpload"
import { FileUpload } from "@/components/knowledge/FileUpload"
import { KnowledgeSearch } from "@/components/knowledge/KnowledgeSearch"
import { ToolList } from "@/components/knowledge/ToolList"
import { ToolForm } from "@/components/knowledge/ToolForm"
import { DocumentPreview } from "@/components/knowledge/DocumentPreview"
import type { KnowledgeBase, Tool, Document } from "@/lib/types/knowledge"

export default function KnowledgePage() {
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null)
  const [editingKB, setEditingKB] = useState<KnowledgeBase | null>(null)
  const [editingTool, setEditingTool] = useState<Tool | null>(null)
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  const handleSelectKB = (kb: KnowledgeBase) => {
    setSelectedKB(kb)
  }

  const handleEditKB = (kb: KnowledgeBase) => {
    setEditingKB(kb)
    setShowCreateForm(true)
  }

  const handleEditTool = (tool: Tool) => {
    setEditingTool(tool)
  }

  const handleToolFormSuccess = () => {
    setEditingTool(null)
  }

  const handleToolFormCancel = () => {
    setEditingTool(null)
  }

  const handleFormSuccess = () => {
    setShowCreateForm(false)
    setEditingKB(null)
  }

  const handleFormCancel = () => {
    setShowCreateForm(false)
    setEditingKB(null)
  }

  const handleBackToList = () => {
    setSelectedKB(null)
  }

  // Show create/edit form
  if (showCreateForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              {editingKB ? "Edit Knowledge Base" : "Create Knowledge Base"}
            </h1>
            <p className="text-muted-foreground">
              {editingKB
                ? "Update the knowledge base details"
                : "Create a new knowledge base to organize your documents"}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={handleFormCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <KnowledgeBaseForm
          knowledgeBase={editingKB}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
        />
      </div>
    )
  }

  // Show selected knowledge base details and documents
  if (selectedKB) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={handleBackToList}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Knowledge Bases
            </Button>
            <div>
              <h1 className="text-3xl font-bold">{selectedKB.name}</h1>
              {selectedKB.description && (
                <p className="text-muted-foreground">{selectedKB.description}</p>
              )}
            </div>
          </div>
          <Button variant="outline" onClick={() => handleEditKB(selectedKB)}>
            Edit Knowledge Base
          </Button>
        </div>

        {editingTool ? (
          <ToolForm
            tool={editingTool}
            kbId={selectedKB.id}
            onSuccess={handleToolFormSuccess}
            onCancel={handleToolFormCancel}
          />
        ) : (
          <div className="space-y-6">
            <ToolList kbId={selectedKB.id} onEdit={handleEditTool} />
            
            <div className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-4">
                  <FileUpload
                    kbId={selectedKB.id}
                    onSuccess={() => {
                      // Documents will automatically refresh via query invalidation
                    }}
                  />
                </div>
                <div className="space-y-4">
                  <DocumentUpload
                    kbId={selectedKB.id}
                    onSuccess={() => {
                      // Documents will automatically refresh via query invalidation
                    }}
                  />
                </div>
              </div>
              <DocumentList
                kbId={selectedKB.id}
                onPreview={(doc) => setPreviewDoc(doc)}
              />
              <KnowledgeSearch kbId={selectedKB.id} />
            </div>
          </div>
        )}

        <DocumentPreview
          document={previewDoc}
          open={!!previewDoc}
          onClose={() => setPreviewDoc(null)}
        />
      </div>
    )
  }

  // Show knowledge bases list
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Bases</h1>
          <p className="text-muted-foreground">
            Manage your knowledge bases and documents
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Knowledge Base
        </Button>
      </div>

      <KnowledgeBaseList
        onSelect={handleSelectKB}
        selectedId={selectedKB?.id}
        onEdit={handleEditKB}
      />
    </div>
  )
}
