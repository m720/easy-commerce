import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Tag } from "@/types"

export const useTags = () =>
  useQuery({
    queryKey: ["tags"],
    queryFn: () => api.get<Tag[]>("/tags").then((r) => r.data),
  })

export const useCreateTag = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; slug: string }) =>
      api.post<Tag>("/tags", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  })
}

export const useUpdateTag = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; name?: string; slug?: string }) =>
      api.put<Tag>(`/tags/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  })
}

export const useDeleteTag = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/tags/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  })
}
