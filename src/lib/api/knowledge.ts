import { apiClient } from "./client"
import type {
  KnowledgeBase,
  KnowledgeBaseCreate,
  KnowledgeBaseUpdate,
  Document,
  DocumentUploadRequest,
  DocumentUploadResponse,
  Tool,
  ToolUpdate,
} from "@/lib/types/knowledge"

export const knowledgeApi = {
  // Knowledge Base endpoints
  listKnowledgeBases: () =>
    apiClient.get<KnowledgeBase[]>("/knowledge/knowledge-bases"),
  getKnowledgeBase: (id: string) =>
    apiClient.get<KnowledgeBase>(`/knowledge/knowledge-bases/${id}`),
  createKnowledgeBase: (data: KnowledgeBaseCreate) =>
    apiClient.post<KnowledgeBase>("/knowledge/knowledge-bases", data),
  updateKnowledgeBase: (id: string, data: KnowledgeBaseUpdate) =>
    apiClient.put<KnowledgeBase>(`/knowledge/knowledge-bases/${id}`, data),
  deleteKnowledgeBase: (id: string) =>
    apiClient.delete(`/knowledge/knowledge-bases/${id}`),

  // Document endpoints
  listDocuments: (kbId: string) =>
    apiClient.get<Document[]>(`/knowledge/knowledge-bases/${kbId}/documents`),
  uploadDocuments: (kbId: string, data: DocumentUploadRequest) =>
    apiClient.post<DocumentUploadResponse>(
      `/knowledge/knowledge-bases/${kbId}/documents`,
      data
    ),
  deleteDocument: (kbId: string, docId: string) =>
    apiClient.delete(
      `/knowledge/knowledge-bases/${kbId}/documents/${docId}`
    ),
  bulkDeleteDocuments: (kbId: string, documentIds: string[]) =>
    apiClient.post(`/knowledge/knowledge-bases/${kbId}/documents/bulk-delete`, {
      document_ids: documentIds,
    }),
  uploadFiles: (
    kbId: string,
    formData: FormData
  ) =>
    apiClient.post<DocumentUploadResponse>(
      `/knowledge/knowledge-bases/${kbId}/documents/upload-files`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    ),

  // Tool endpoints
  listTools: (kbId: string) =>
    apiClient.get<Tool[]>(`/knowledge/knowledge-bases/${kbId}/tools`),
  updateTool: (kbId: string, toolId: string, data: ToolUpdate) =>
    apiClient.put<Tool>(`/knowledge/knowledge-bases/${kbId}/tools/${toolId}`, data),
  deleteTool: (kbId: string, toolId: string) =>
    apiClient.delete(`/knowledge/knowledge-bases/${kbId}/tools/${toolId}`),
}
