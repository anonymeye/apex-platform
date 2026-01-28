"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useUploadDocuments } from "@/lib/hooks/useKnowledge"
import type { DocumentUploadRequest } from "@/lib/types/knowledge"
import { Upload, Loader2, Plus, X } from "lucide-react"

interface DocumentUploadProps {
  kbId: string
  onSuccess?: () => void
}

export function DocumentUpload({ kbId, onSuccess }: DocumentUploadProps) {
  const uploadMutation = useUploadDocuments()
  const [documents, setDocuments] = useState<
    Array<{ content: string; source: string; metadata: Record<string, any> }>
  >([{ content: "", source: "", metadata: {} }])
  const [chunkSize, setChunkSize] = useState(1000)
  const [chunkOverlap, setChunkOverlap] = useState(200)
  const [autoCreateTool, setAutoCreateTool] = useState(true)

  const addDocument = () => {
    setDocuments([...documents, { content: "", source: "", metadata: {} }])
  }

  const removeDocument = (index: number) => {
    setDocuments(documents.filter((_, i) => i !== index))
  }

  const updateDocument = (
    index: number,
    field: "content" | "source",
    value: string
  ) => {
    const updated = [...documents]
    updated[index] = { ...updated[index], [field]: value }
    setDocuments(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const validDocuments = documents.filter((doc) => doc.content.trim())
    if (validDocuments.length === 0) {
      alert("Please add at least one document with content")
      return
    }

    try {
      const uploadData: DocumentUploadRequest = {
        documents: validDocuments.map((doc) => ({
          content: doc.content,
          source: doc.source || null,
          metadata: doc.metadata,
        })),
        auto_create_tool: autoCreateTool,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      }

      await uploadMutation.mutateAsync({
        kbId,
        data: uploadData,
      })

      // Reset form
      setDocuments([{ content: "", source: "", metadata: {} }])
      setChunkSize(1000)
      setChunkOverlap(200)

      onSuccess?.()
    } catch (error) {
      console.error("Failed to upload documents:", error)
      alert("Failed to upload documents. Please try again.")
    }
  }

  const isLoading = uploadMutation.isPending

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Documents</CardTitle>
        <CardDescription>
          Add documents to this knowledge base. They will be automatically chunked and embedded.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            {documents.map((doc, index) => (
              <div key={index} className="space-y-3 p-4 border rounded-lg">
                <div className="flex items-center justify-between">
                  <Label>Document {index + 1}</Label>
                  {documents.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDocument(index)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`source-${index}`}>Source (optional)</Label>
                  <Input
                    id={`source-${index}`}
                    value={doc.source}
                    onChange={(e) =>
                      updateDocument(index, "source", e.target.value)
                    }
                    placeholder="e.g., document.pdf or https://example.com/doc"
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`content-${index}`}>Content *</Label>
                  <Textarea
                    id={`content-${index}`}
                    value={doc.content}
                    onChange={(e) =>
                      updateDocument(index, "content", e.target.value)
                    }
                    placeholder="Paste or type document content here..."
                    rows={6}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>
            ))}

            <Button
              type="button"
              variant="outline"
              onClick={addDocument}
              disabled={isLoading}
              className="w-full"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Another Document
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="chunk-size">Chunk Size</Label>
              <Input
                id="chunk-size"
                type="number"
                value={chunkSize}
                onChange={(e) => setChunkSize(parseInt(e.target.value) || 1000)}
                min={100}
                max={5000}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="chunk-overlap">Chunk Overlap</Label>
              <Input
                id="chunk-overlap"
                type="number"
                value={chunkOverlap}
                onChange={(e) =>
                  setChunkOverlap(parseInt(e.target.value) || 200)
                }
                min={0}
                max={500}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="auto-create-tool"
              checked={autoCreateTool}
              onChange={(e) => setAutoCreateTool(e.target.checked)}
              disabled={isLoading}
              className="h-4 w-4"
            />
            <Label htmlFor="auto-create-tool" className="cursor-pointer">
              Automatically create RAG tool for this knowledge base
            </Label>
          </div>

          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Upload className="mr-2 h-4 w-4" />
            Upload Documents
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
