import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { knowledgeApi } from "@/lib/api/knowledge"
import type {
  KnowledgeBase,
  KnowledgeBaseCreate,
  KnowledgeBaseUpdate,
  Document,
  DocumentUploadRequest,
  Tool,
  ToolUpdate,
} from "@/lib/types/knowledge"

export function useKnowledgeBases() {
  return useQuery({
    queryKey: ["knowledge-bases"],
    queryFn: async () => {
      try {
        const response = await knowledgeApi.listKnowledgeBases()
        return response.data
      } catch (error: any) {
        // Handle 404 as empty array (no knowledge bases yet)
        if (error?.response?.status === 404) {
          return []
        }
        throw error
      }
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 (no knowledge bases is a valid state)
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useKnowledgeBase(kbId: string | null) {
  return useQuery({
    queryKey: ["knowledge-base", kbId],
    queryFn: () => knowledgeApi.getKnowledgeBase(kbId!).then((res) => res.data),
    enabled: !!kbId,
  })
}

export function useDocuments(kbId: string | null) {
  return useQuery({
    queryKey: ["documents", kbId],
    queryFn: () => knowledgeApi.listDocuments(kbId!).then((res) => res.data),
    enabled: !!kbId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: KnowledgeBaseCreate) =>
      knowledgeApi.createKnowledgeBase(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}

export function useUpdateKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: KnowledgeBaseUpdate }) =>
      knowledgeApi.updateKnowledgeBase(id, data).then((res) => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
      queryClient.invalidateQueries({ queryKey: ["knowledge-base", variables.id] })
    },
  })
}

export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteKnowledgeBase(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] })
    },
  })
}

export function useUploadDocuments() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      kbId,
      data,
    }: {
      kbId: string
      data: DocumentUploadRequest
    }) => knowledgeApi.uploadDocuments(kbId, data).then((res) => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["documents", variables.kbId] })
      queryClient.invalidateQueries({ queryKey: ["knowledge-base", variables.kbId] })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ kbId, docId }: { kbId: string; docId: string }) =>
      knowledgeApi.deleteDocument(kbId, docId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["documents", variables.kbId] })
    },
  })
}

export function useTools(kbId: string | null) {
  return useQuery({
    queryKey: ["tools", kbId],
    queryFn: () => knowledgeApi.listTools(kbId!).then((res) => res.data),
    enabled: !!kbId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useUpdateTool() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      kbId,
      toolId,
      data,
    }: {
      kbId: string
      toolId: string
      data: ToolUpdate
    }) => knowledgeApi.updateTool(kbId, toolId, data).then((res) => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["tools", variables.kbId] })
    },
  })
}

export function useDeleteTool() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ kbId, toolId }: { kbId: string; toolId: string }) =>
      knowledgeApi.deleteTool(kbId, toolId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["tools", variables.kbId] })
    },
  })
}
