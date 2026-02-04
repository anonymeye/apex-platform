import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toolsApi } from "@/lib/api/tools"
import type { ToolCreate, ToolUpdate } from "@/lib/types/tools"

const TOOLS_QUERY_KEY = "tools-list"

export function useToolsList(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: [TOOLS_QUERY_KEY, params?.skip ?? 0, params?.limit ?? 100],
    queryFn: async () => {
      const response = await toolsApi.list(params)
      return response.data
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useTool(id: string | null) {
  return useQuery({
    queryKey: ["tool", id],
    queryFn: () => toolsApi.get(id!).then((res) => res.data),
    enabled: !!id,
  })
}

export function useCreateTool() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ToolCreate) => toolsApi.create(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOLS_QUERY_KEY] })
    },
  })
}

export function useUpdateTool() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ToolUpdate }) =>
      toolsApi.update(id, data).then((res) => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [TOOLS_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: ["tool", variables.id] })
    },
  })
}

export function useDeleteTool() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => toolsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TOOLS_QUERY_KEY] })
    },
  })
}
