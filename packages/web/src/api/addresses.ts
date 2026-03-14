import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Address, UUID } from "@/types"

export const useAddresses = () =>
  useQuery({
    queryKey: ["addresses"],
    queryFn: () => api.get<Address[]>("/addresses").then((r) => r.data),
  })

export const useCreateAddress = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { label?: string; street: string; city: string; state?: string; country: string; postal_code: string; is_default?: boolean }) =>
      api.post<Address>("/addresses", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addresses"] }),
  })
}

export const useUpdateAddress = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: UUID; label?: string; street?: string; city?: string; state?: string; country?: string; postal_code?: string; is_default?: boolean }) =>
      api.put<Address>(`/addresses/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addresses"] }),
  })
}

export const useDeleteAddress = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/addresses/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addresses"] }),
  })
}

export const useSetDefaultAddress = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.patch<Address>(`/addresses/${id}/set-default`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["addresses"] }),
  })
}
