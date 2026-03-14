import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { ReturnRequest, UUID, PaginationParams } from "@/types"

export const useSubmitReturn = (orderId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { reason: string; items: Array<{ order_item_id: UUID; quantity: number }> }) =>
      api.post<ReturnRequest>(`/orders/${orderId}/returns`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orders", orderId] }),
  })
}

export const useReturnRequest = (orderId: UUID, returnId: UUID) =>
  useQuery({
    queryKey: ["returns", orderId, returnId],
    queryFn: () => api.get<ReturnRequest>(`/orders/${orderId}/returns/${returnId}`).then((r) => r.data),
    enabled: !!orderId && !!returnId,
  })

export const useAdminReturns = (params?: PaginationParams) =>
  useQuery({
    queryKey: ["admin-returns", params],
    queryFn: () => api.get<ReturnRequest[]>("/orders/admin/returns", { params }).then((r) => r.data),
  })

export const useApproveReturn = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ returnId, admin_notes }: { returnId: UUID; admin_notes?: string }) =>
      api.patch<ReturnRequest>(`/orders/admin/returns/${returnId}/approve`, { admin_notes }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-returns"] }),
  })
}

export const useRejectReturn = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ returnId, admin_notes }: { returnId: UUID; admin_notes?: string }) =>
      api.patch<ReturnRequest>(`/orders/admin/returns/${returnId}/reject`, { admin_notes }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-returns"] }),
  })
}
