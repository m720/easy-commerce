import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import type { Product, ProductVariant, ProductImage, PaginationParams, UUID } from "@/types"

interface ProductFilter extends PaginationParams {
  search?: string
  category_id?: number
  tag_id?: number
  min_price?: number
  max_price?: number
  is_featured?: boolean
}

export const useProducts = (params?: ProductFilter) =>
  useQuery({
    queryKey: ["products", params],
    queryFn: () => api.get<Product[]>("/products", { params }).then((r) => r.data),
  })

export const useProduct = (id: UUID) =>
  useQuery({
    queryKey: ["products", id],
    queryFn: () => api.get<Product>(`/products/${id}`).then((r) => r.data),
    enabled: !!id,
  })

export const useFeaturedProducts = (params?: PaginationParams) =>
  useQuery({
    queryKey: ["products", "featured", params],
    queryFn: () => api.get<Product[]>("/products/featured", { params }).then((r) => r.data),
  })

export const useCreateProduct = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string; base_price: string; category_id?: number; is_featured?: boolean; tag_ids?: number[] }) =>
      api.post<Product>("/products", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  })
}

export const useUpdateProduct = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: UUID; name?: string; description?: string; base_price?: string; category_id?: number; is_featured?: boolean; is_active?: boolean; tag_ids?: number[] }) =>
      api.put<Product>(`/products/${id}`, data).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["products"] })
      qc.invalidateQueries({ queryKey: ["products", vars.id] })
    },
  })
}

export const useDeleteProduct = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.delete(`/products/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  })
}

export const useToggleFeature = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: UUID) => api.patch<Product>(`/products/${id}/feature`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  })
}

export const useBulkActivate = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (product_ids: UUID[]) => api.post<{ updated: number }>("/products/bulk-activate", { product_ids }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  })
}

export const useBulkDeactivate = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (product_ids: UUID[]) => api.post<{ updated: number }>("/products/bulk-deactivate", { product_ids }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  })
}

// Variants
export const useProductVariants = (productId: UUID) =>
  useQuery({
    queryKey: ["variants", productId],
    queryFn: () => api.get<ProductVariant[]>(`/products/${productId}/variants`).then((r) => r.data),
    enabled: !!productId,
  })

export const useCreateVariant = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; sku: string; price: string; stock_quantity?: number; low_stock_threshold?: number }) =>
      api.post<ProductVariant>(`/products/${productId}/variants`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["variants", productId] })
      qc.invalidateQueries({ queryKey: ["products", productId] })
    },
  })
}

export const useUpdateVariant = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ variantId, ...data }: { variantId: UUID; name?: string; sku?: string; price?: string; stock_quantity?: number; low_stock_threshold?: number }) =>
      api.put<ProductVariant>(`/products/${productId}/variants/${variantId}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["variants", productId] })
      qc.invalidateQueries({ queryKey: ["products", productId] })
    },
  })
}

export const useDeleteVariant = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (variantId: UUID) => api.delete(`/products/${productId}/variants/${variantId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["variants", productId] })
      qc.invalidateQueries({ queryKey: ["products", productId] })
    },
  })
}

// Images
export const useProductImages = (productId: UUID) =>
  useQuery({
    queryKey: ["images", productId],
    queryFn: () => api.get<ProductImage[]>(`/products/${productId}/images`).then((r) => r.data),
    enabled: !!productId,
  })

export const useGetUploadUrl = (productId: UUID) =>
  useMutation({
    mutationFn: (data: { filename: string; content_type?: string }) =>
      api.post<{ upload_url: string; s3_key: string }>(`/products/${productId}/images/upload-url`, data).then((r) => r.data),
  })

export const useConfirmUpload = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { s3_key: string; is_primary?: boolean; sort_order?: number }) =>
      api.post<ProductImage>(`/products/${productId}/images`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["images", productId] }),
  })
}

export const useSetPrimaryImage = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (imageId: UUID) => api.patch<ProductImage>(`/products/${productId}/images/${imageId}/primary`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["images", productId] }),
  })
}

export const useDeleteImage = (productId: UUID) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (imageId: UUID) => api.delete(`/products/${productId}/images/${imageId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["images", productId] }),
  })
}
