import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Category, Product, PaginationParams } from "@/types"

export const useCategories = () =>
  useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories").then((r) => r.data),
  })

export const useCategory = (id: number) =>
  useQuery({
    queryKey: ["categories", id],
    queryFn: () => api.get<Category>(`/categories/${id}`).then((r) => r.data),
    enabled: !!id,
  })

export const useCategoryProducts = (id: number, params?: PaginationParams) =>
  useQuery({
    queryKey: ["categories", id, "products", params],
    queryFn: () => api.get<Product[]>(`/categories/${id}/products`, { params }).then((r) => r.data),
    enabled: !!id,
  })

export const useCreateCategory = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; slug: string; description?: string }) =>
      api.post<Category>("/categories", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  })
}

export const useUpdateCategory = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; name?: string; slug?: string; description?: string }) =>
      api.put<Category>(`/categories/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  })
}

export const useDeleteCategory = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete(`/categories/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  })
}
