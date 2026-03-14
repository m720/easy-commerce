import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Wishlist, UUID } from "@/types"
import { useAuthStore } from "@/store/authStore"

export const useWishlist = () => {
  const token = useAuthStore((s) => s.token)
  return useQuery({
    queryKey: ["wishlist"],
    queryFn: () => api.get<Wishlist>("/wishlist").then((r) => r.data),
    enabled: !!token,
  })
}

export const useAddToWishlist = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (product_id: UUID) => api.post("/wishlist", { product_id }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wishlist"] }),
  })
}

export const useRemoveFromWishlist = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: UUID) => api.delete(`/wishlist/${itemId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wishlist"] }),
  })
}

export const useMoveToCart = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: UUID) => api.post(`/wishlist/${itemId}/move-to-cart`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wishlist"] })
      qc.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}
