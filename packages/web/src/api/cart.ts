import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Cart, UUID } from "@/types"
import { useAuthStore } from "@/store/authStore"

export const useCart = () => {
  const token = useAuthStore((s) => s.token)
  return useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/cart").then((r) => r.data),
    enabled: !!token,
  })
}

export const useAddToCart = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { variant_id: UUID; quantity?: number }) =>
      api.post<Cart>("/cart/items", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cart"] }),
  })
}

export const useUpdateCartItem = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: UUID; quantity: number }) =>
      api.put<Cart>(`/cart/items/${itemId}`, { quantity }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cart"] }),
  })
}

export const useRemoveCartItem = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: UUID) => api.delete(`/cart/items/${itemId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cart"] }),
  })
}

export const useClearCart = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.delete("/cart"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cart"] }),
  })
}
