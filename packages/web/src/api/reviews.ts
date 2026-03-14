import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Review, UUID } from "@/types"

export const useProductReviews = (productId: UUID, params?: { sort_by?: "created_at" | "rating"; skip?: number; limit?: number }) =>
  useQuery({
    queryKey: ["reviews", productId, params],
    queryFn: () => api.get<Review[]>(`/products/${productId}/reviews`, { params }).then((r) => r.data),
    enabled: !!productId,
  })

export const useCreateReview = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { rating: number; comment?: string }) =>
      api.post<Review>(`/products/${productId}/reviews`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", productId] }),
  })
}

export const useUpdateReview = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ reviewId, ...data }: { reviewId: UUID; rating?: number; comment?: string }) =>
      api.put<Review>(`/products/${productId}/reviews/${reviewId}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", productId] }),
  })
}

export const useDeleteReview = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (reviewId: UUID) => api.delete(`/products/${productId}/reviews/${reviewId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", productId] }),
  })
}

export const useApproveReview = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (reviewId: UUID) => api.patch<Review>(`/products/${productId}/reviews/${reviewId}/approve`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", productId] }),
  })
}

export const useHideReview = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (reviewId: UUID) => api.patch<Review>(`/products/${productId}/reviews/${reviewId}/hide`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", productId] }),
  })
}
