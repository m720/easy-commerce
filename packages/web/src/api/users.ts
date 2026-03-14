import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { User, UUID, PaginationParams } from "@/types"

export const useUsers = (params?: PaginationParams) =>
  useQuery({
    queryKey: ["users", params],
    queryFn: () => api.get<User[]>("/users", { params }).then((r) => r.data),
  })

export const useUser = (id: UUID) =>
  useQuery({
    queryKey: ["users", id],
    queryFn: () => api.get<User>(`/users/${id}`).then((r) => r.data),
    enabled: !!id,
  })

export const useActivateUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.patch<User>(`/users/${id}/activate`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  })
}

export const useDeactivateUser = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.patch<User>(`/users/${id}/deactivate`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  })
}
