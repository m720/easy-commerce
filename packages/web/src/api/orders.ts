import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Order, OrderStatus, UUID, PaginationParams } from "@/types"

export const useOrders = (params?: PaginationParams) =>
  useQuery({
    queryKey: ["orders", params],
    queryFn: () => api.get<Order[]>("/orders", { params }).then((r) => r.data),
  })

export const useOrder = (id: UUID) =>
  useQuery({
    queryKey: ["orders", id],
    queryFn: () => api.get<Order>(`/orders/${id}`).then((r) => r.data),
    enabled: !!id,
  })

export const usePlaceOrder = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { address_id: UUID; coupon_code?: string }) =>
      api.post<Order>("/orders", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] })
      qc.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}

export const useCancelOrder = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/orders/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }),
  })
}

export const useAdminOrders = (params?: { status?: OrderStatus; user_id?: UUID; from_date?: string; to_date?: string } & PaginationParams) =>
  useQuery({
    queryKey: ["admin-orders", params],
    queryFn: () => api.get<Order[]>("/orders/admin/all", { params }).then((r) => r.data),
  })

export const useUpdateOrderStatus = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: UUID; status: OrderStatus }) =>
      api.patch<Order>(`/orders/admin/${id}/status`, { status }).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["admin-orders"] })
      qc.invalidateQueries({ queryKey: ["orders", vars.id] })
    },
  })
}
