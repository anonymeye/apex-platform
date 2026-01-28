"use client"

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { FileText, X } from "lucide-react"
import type { Document } from "@/lib/types/knowledge"

interface DocumentPreviewProps {
  document: Document | null
  open: boolean
  onClose: () => void
}

export function DocumentPreview({ document, open, onClose }: DocumentPreviewProps) {
  if (!document) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {document.source || `Document ${document.chunk_index !== null ? `(Chunk ${document.chunk_index})` : document.id.slice(0, 8)}`}
          </DialogTitle>
          <DialogDescription>
            {document.chunk_index !== null && `Chunk ${document.chunk_index}`}
            {document.metadata && Object.keys(document.metadata).length > 0 && (
              <span className="ml-2">
                • {Object.keys(document.metadata).length} metadata field(s)
              </span>
            )}
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto mt-4">
          <div className="space-y-4">
            {/* Metadata */}
            {document.metadata && Object.keys(document.metadata).length > 0 && (
              <div className="border rounded-lg p-4 bg-muted/50">
                <h3 className="font-semibold mb-2 text-sm">Metadata</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(document.metadata).map(([key, value]) => (
                    <div key={key}>
                      <span className="font-medium">{key}:</span>{" "}
                      <span className="text-muted-foreground">
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Content */}
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-sm">Content</h3>
              <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
                {document.content}
              </div>
            </div>

            {/* Additional Info */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>ID: {document.id}</div>
              {document.vector_id && <div>Vector ID: {document.vector_id}</div>}
              <div>Created: {new Date(document.created_at).toLocaleString()}</div>
              <div>Updated: {new Date(document.updated_at).toLocaleString()}</div>
            </div>
          </div>
        </div>
        <div className="flex justify-end mt-4 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
