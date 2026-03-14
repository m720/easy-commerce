import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Coupon, CouponValidateResponse, CouponType, PaginationParams, UUID } from "@/types"

export const useValidateCoupon = () =>
  useMutation({
    mutationFn: (data: { code: string; order_subtotal: string }) =>
      api.post<CouponValidateResponse>("/coupons/validate", data).then((r) => r.data),
  })

export const useCoupons = (params?: PaginationParams) =>
  useQuery({
    queryKey: ["coupons", params],
    queryFn: () => api.get<Coupon[]>("/coupons", { params }).then((r) => r.data),
  })

export const useCreateCoupon = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { code: string; type: CouponType; value: string; min_order_amount?: string; max_uses?: number; expires_at?: string; is_active?: boolean }) =>
      api.post<Coupon>("/coupons", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["coupons"] }),
  })
}

export const useUpdateCoupon = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: UUID; code?: string; type?: CouponType; value?: string; min_order_amount?: string; max_uses?: number; expires_at?: string; is_active?: boolean }) =>
      api.put<Coupon>(`/coupons/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["coupons"] }),
  })
}

export const useDeleteCoupon = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/coupons/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["coupons"] }),
  })
}
