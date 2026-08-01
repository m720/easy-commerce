import { useState, useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { Plus, Trash2, Star } from "lucide-react"
import {
  useProduct,
  useCreateProduct,
  useUpdateProduct,
  useProductVariants,
  useCreateVariant,
  useUpdateVariant,
  useDeleteVariant,
  useProductImages,
  useGetUploadUrl,
  useConfirmUpload,
  useSetPrimaryImage,
  useDeleteImage,
} from "@/api/products"
import { useCategories } from "@/api/categories"
import { useTags } from "@/api/tags"
import { formatPrice } from "@/lib/utils"
import type { UUID } from "@/types"

interface ProductFormValues {
  name: string
  description: string
  base_price: string
  category_id: string
  is_featured: boolean
  is_active: boolean
  tag_ids: number[]
}

interface VariantFormValues {
  name: string
  sku: string
  price: string
  stock_quantity: number
  low_stock_threshold: number
}

export default function ProductFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id && id !== "new"
  const navigate = useNavigate()

  const { data: product, isLoading: productLoading } = useProduct(isEdit ? id! : "")
  const { data: categories } = useCategories()
  const { data: tags } = useTags()
  const { data: variants } = useProductVariants(isEdit ? id! : "")
  const { data: images } = useProductImages(isEdit ? id! : "")

  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()

  const createVariant = useCreateVariant(isEdit ? id! : "")
  const updateVariant = useUpdateVariant(isEdit ? id! : "")
  const deleteVariant = useDeleteVariant(isEdit ? id! : "")

  const getUploadUrl = useGetUploadUrl(isEdit ? id! : "")
  const confirmUpload = useConfirmUpload(isEdit ? id! : "")
  const setPrimaryImage = useSetPrimaryImage(isEdit ? id! : "")
  const deleteImage = useDeleteImage(isEdit ? id! : "")

  const [showVariantForm, setShowVariantForm] = useState(false)
  const [editingVariantId, setEditingVariantId] = useState<UUID | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
    reset: resetForm,
  } = useForm<ProductFormValues>({
    defaultValues: {
      name: "",
      description: "",
      base_price: "",
      category_id: "",
      is_featured: false,
      is_active: true,
      tag_ids: [],
    },
    values: product
      ? {
          name: product.name,
          description: product.description ?? "",
          base_price: product.base_price,
          category_id: product.category_id ? String(product.category_id) : "",
          is_featured: product.is_featured,
          is_active: product.is_active,
          tag_ids: product.tags.map((t) => t.id),
        }
      : undefined,
  })

  const watchedTagIds = watch("tag_ids") || []

  const variantForm = useForm<VariantFormValues>({
    defaultValues: { name: "", sku: "", price: "", stock_quantity: 0, low_stock_threshold: 5 },
  })

  const onSubmit = async (data: ProductFormValues) => {
    const payload = {
      name: data.name,
      description: data.description || undefined,
      base_price: data.base_price,
      category_id: data.category_id ? Number(data.category_id) : undefined,
      is_featured: data.is_featured,
      tag_ids: data.tag_ids,
    }

    if (isEdit) {
      await updateProduct.mutateAsync({ id: id!, ...payload, is_active: data.is_active })
      navigate("/admin/products")
    } else {
      await createProduct.mutateAsync(payload)
      navigate("/admin/products")
    }
  }

  const onVariantSubmit = async (data: VariantFormValues) => {
    if (editingVariantId) {
      await updateVariant.mutateAsync({ variantId: editingVariantId, ...data })
    } else {
      await createVariant.mutateAsync(data)
    }
    variantForm.reset()
    setShowVariantForm(false)
    setEditingVariantId(null)
  }

  const handleEditVariant = (v: typeof variants extends (infer T)[] | undefined ? T : never) => {
    if (!v) return
    variantForm.reset({
      name: (v as any).name,
      sku: (v as any).sku,
      price: (v as any).price,
      stock_quantity: (v as any).stock_quantity,
      low_stock_threshold: (v as any).low_stock_threshold,
    })
    setEditingVariantId((v as any).id)
    setShowVariantForm(true)
  }

  const handleDeleteVariant = (variantId: UUID, name: string) => {
    if (window.confirm(`Delete variant "${name}"?`)) {
      deleteVariant.mutate(variantId)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !isEdit) return
    setUploading(true)
    try {
      const { upload_url, s3_key } = await getUploadUrl.mutateAsync({
        filename: file.name,
        content_type: file.type,
      })
      await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } })
      await confirmUpload.mutateAsync({ s3_key, is_primary: !images || images.length === 0 })
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  const toggleTag = (tagId: number) => {
    const current = watchedTagIds
    if (current.includes(tagId)) {
      setValue("tag_ids", current.filter((id) => id !== tagId))
    } else {
      setValue("tag_ids", [...current, tagId])
    }
  }

  if (isEdit && productLoading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-48 bg-zinc-200 animate-pulse rounded" />
        <div className="h-64 bg-zinc-100 animate-pulse rounded-xl" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-zinc-900">
        {isEdit ? `Edit: ${product?.name ?? "Product"}` : "New Product"}
      </h1>

      {/* Product Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">Name *</label>
          <input
            {...register("name", { required: "Name is required" })}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">Description</label>
          <textarea
            {...register("description")}
            rows={4}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-y"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Base Price *</label>
            <input
              {...register("base_price", { required: "Price is required" })}
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            {errors.base_price && <p className="text-red-500 text-xs mt-1">{errors.base_price.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Category</label>
            <select
              {...register("category_id")}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
            >
              <option value="">No category</option>
              {categories?.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-2">Tags</label>
          <div className="flex flex-wrap gap-2">
            {tags?.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.id)}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  watchedTagIds.includes(tag.id)
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-zinc-600 border-zinc-300 hover:border-indigo-400"
                }`}
              >
                {tag.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" {...register("is_featured")} className="rounded border-zinc-300" />
            <span className="text-sm font-medium text-zinc-700">Featured</span>
          </label>
          {isEdit && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" {...register("is_active")} className="rounded border-zinc-300" />
              <span className="text-sm font-medium text-zinc-700">Active</span>
            </label>
          )}
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? "Saving..." : isEdit ? "Save Changes" : "Create Product"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/admin/products")}
            className="border px-6 py-2 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Variants (edit mode only) */}
      {isEdit && (
        <div className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900">Variants</h2>
            <button
              onClick={() => {
                variantForm.reset({ name: "", sku: "", price: "", stock_quantity: 0, low_stock_threshold: 5 })
                setEditingVariantId(null)
                setShowVariantForm(!showVariantForm)
              }}
              className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              <Plus size={15} /> Add Variant
            </button>
          </div>

          {showVariantForm && (
            <form
              onSubmit={variantForm.handleSubmit(onVariantSubmit)}
              className="bg-zinc-50 border rounded-lg p-4 space-y-3"
            >
              <h3 className="text-sm font-medium text-zinc-700">
                {editingVariantId ? "Edit Variant" : "New Variant"}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-zinc-600 mb-1 block">Name *</label>
                  <input
                    {...variantForm.register("name", { required: true })}
                    className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-600 mb-1 block">SKU *</label>
                  <input
                    {...variantForm.register("sku", { required: true })}
                    className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-600 mb-1 block">Price *</label>
                  <input
                    {...variantForm.register("price", { required: true })}
                    type="number"
                    step="0.01"
                    min="0"
                    className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-600 mb-1 block">Stock</label>
                  <input
                    {...variantForm.register("stock_quantity", { valueAsNumber: true })}
                    type="number"
                    min="0"
                    className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-600 mb-1 block">Low Stock Threshold</label>
                  <input
                    {...variantForm.register("low_stock_threshold", { valueAsNumber: true })}
                    type="number"
                    min="0"
                    className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={variantForm.formState.isSubmitting}
                  className="bg-indigo-600 text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  {editingVariantId ? "Update" : "Add"}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowVariantForm(false); setEditingVariantId(null) }}
                  className="border px-4 py-1.5 rounded text-sm hover:bg-zinc-100"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {!variants || variants.length === 0 ? (
            <p className="text-sm text-zinc-500 py-4 text-center">No variants yet. Add one above.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 border-b">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-zinc-600">Name</th>
                    <th className="px-3 py-2 text-left font-medium text-zinc-600">SKU</th>
                    <th className="px-3 py-2 text-right font-medium text-zinc-600">Price</th>
                    <th className="px-3 py-2 text-right font-medium text-zinc-600">Stock</th>
                    <th className="px-3 py-2 text-right font-medium text-zinc-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((v) => (
                    <tr key={v.id} className="border-b last:border-0">
                      <td className="px-3 py-2 text-zinc-900">{v.name}</td>
                      <td className="px-3 py-2 font-mono text-xs text-zinc-500">{v.sku}</td>
                      <td className="px-3 py-2 text-right">{formatPrice(v.price)}</td>
                      <td className="px-3 py-2 text-right">{v.stock_quantity}</td>
                      <td className="px-3 py-2">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleEditVariant(v)}
                            className="p-1 text-zinc-500 hover:text-indigo-600 rounded"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                          </button>
                          <button
                            onClick={() => handleDeleteVariant(v.id, v.name)}
                            className="p-1 text-zinc-500 hover:text-red-600 rounded"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Images (edit mode only) */}
      {isEdit && (
        <div className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900">Images</h2>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 font-medium disabled:opacity-50"
            >
              <Plus size={15} /> {uploading ? "Uploading..." : "Add Image"}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {!images || images.length === 0 ? (
            <p className="text-sm text-zinc-500 py-4 text-center">No images yet. Upload one above.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {images.map((img) => (
                <div key={img.id} className="relative group rounded-lg overflow-hidden border bg-zinc-50">
                  {img.url ? (
                    <img src={img.url} alt="Product" className="w-full h-32 object-cover" />
                  ) : (
                    <div className="w-full h-32 flex items-center justify-center text-zinc-400 text-xs">
                      No preview
                    </div>
                  )}
                  {img.is_primary && (
                    <div className="absolute top-1 left-1 bg-yellow-400 rounded px-1.5 py-0.5 text-xs font-medium text-yellow-900 flex items-center gap-0.5">
                      <Star size={10} className="fill-yellow-900" /> Primary
                    </div>
                  )}
                  <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {!img.is_primary && (
                      <button
                        onClick={() => setPrimaryImage.mutate(img.id)}
                        className="bg-white/90 rounded p-1 hover:bg-yellow-50"
                        title="Set as primary"
                      >
                        <Star size={12} className="text-yellow-500" />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (window.confirm("Delete this image?")) deleteImage.mutate(img.id)
                      }}
                      className="bg-white/90 rounded p-1 hover:bg-red-50"
                      title="Delete"
                    >
                      <Trash2 size={12} className="text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
