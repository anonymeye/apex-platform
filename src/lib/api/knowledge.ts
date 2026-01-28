import { apiClient } from "./client"
import type {
  KnowledgeBase,
  KnowledgeBaseCreate,
  KnowledgeBaseUpdate,
  Document,
  DocumentUploadRequest,
  DocumentUploadResponse,
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
}
