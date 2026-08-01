import { useState } from "react"
import { Link } from "react-router-dom"
import { Plus, Star, Trash2, Pencil } from "lucide-react"
import { useProducts, useDeleteProduct, useToggleFeature, useBulkActivate, useBulkDeactivate } from "@/api/products"
import { formatPrice } from "@/lib/utils"
import { usePagination } from "@/hooks/usePagination"
import PaginationControls from "@/components/shared/PaginationControls"
import type { UUID } from "@/types"

export default function AdminProductsPage() {
  const [search, setSearch] = useState("")
  const [searchInput, setSearchInput] = useState("")
  const [selected, setSelected] = useState<UUID[]>([])
  const { skip, limit, page, nextPage, prevPage, reset } = usePagination(20)

  const { data: products, isLoading } = useProducts({ search, skip, limit })
  const deleteProduct = useDeleteProduct()
  const toggleFeature = useToggleFeature()
  const bulkActivate = useBulkActivate()
  const bulkDeactivate = useBulkDeactivate()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    reset()
  }

  const handleDelete = (id: UUID, name: string) => {
    if (window.confirm(`Delete "${name}"? This cannot be undone.`)) {
      deleteProduct.mutate(id)
    }
  }

  const toggleSelect = (id: UUID) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
  }

  const toggleSelectAll = () => {
    if (!products) return
    if (selected.length === products.length) {
      setSelected([])
    } else {
      setSelected(products.map((p) => p.id))
    }
  }

  const handleBulkActivate = () => {
    if (selected.length === 0) return
    bulkActivate.mutate(selected, { onSuccess: () => setSelected([]) })
  }

  const handleBulkDeactivate = () => {
    if (selected.length === 0) return
    bulkDeactivate.mutate(selected, { onSuccess: () => setSelected([]) })
  }

  const allSelected = products && products.length > 0 && selected.length === products.length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-900">Products</h1>
        <Link
          to="/admin/products/new"
          className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} /> New Product
        </Link>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search products..."
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <button
          type="submit"
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Search
        </button>
        {search && (
          <button
            type="button"
            onClick={() => { setSearch(""); setSearchInput(""); reset() }}
            className="border px-4 py-2 rounded-lg text-sm hover:bg-zinc-50"
          >
            Clear
          </button>
        )}
      </form>

      {/* Bulk Actions */}
      {selected.length > 0 && (
        <div className="flex items-center gap-3 bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-2">
          <span className="text-sm text-indigo-700 font-medium">{selected.length} selected</span>
          <button
            onClick={handleBulkActivate}
            disabled={bulkActivate.isPending}
            className="text-sm text-green-700 hover:text-green-900 font-medium disabled:opacity-50"
          >
            Activate
          </button>
          <button
            onClick={handleBulkDeactivate}
            disabled={bulkDeactivate.isPending}
            className="text-sm text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
          >
            Deactivate
          </button>
          <button
            onClick={() => setSelected([])}
            className="text-sm text-zinc-500 hover:text-zinc-700 ml-auto"
          >
            Clear
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 bg-zinc-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !products || products.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">
            <p className="text-lg font-medium">No products found</p>
            <p className="text-sm mt-1">Try adjusting your search or create a new product.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={!!allSelected}
                      onChange={toggleSelectAll}
                      className="rounded border-zinc-300"
                    />
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Category</th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Base Price</th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Variants</th>
                  <th className="px-4 py-3 text-center font-medium text-zinc-600">Featured</th>
                  <th className="px-4 py-3 text-center font-medium text-zinc-600">Active</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id} className="border-b last:border-0 hover:bg-zinc-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(product.id)}
                        onChange={() => toggleSelect(product.id)}
                        className="rounded border-zinc-300"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-zinc-900">{product.name}</div>
                      {product.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {product.tags.map((tag) => (
                            <span key={tag.id} className="text-xs bg-zinc-100 text-zinc-600 px-1.5 py-0.5 rounded">
                              {tag.name}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-zinc-600">
                      {product.category?.name ?? <span className="text-zinc-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-zinc-900 font-medium">
                      {formatPrice(product.base_price)}
                    </td>
                    <td className="px-4 py-3 text-zinc-600">
                      {product.variants.length}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleFeature.mutate(product.id)}
                        disabled={toggleFeature.isPending}
                        title={product.is_featured ? "Remove from featured" : "Mark as featured"}
                        className="disabled:opacity-50"
                      >
                        <Star
                          size={18}
                          className={product.is_featured ? "fill-yellow-400 text-yellow-400" : "text-zinc-300"}
                        />
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          product.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-zinc-100 text-zinc-500"
                        }`}
                      >
                        {product.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/admin/products/${product.id}`}
                          className="p-1.5 text-zinc-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                          title="Edit"
                        >
                          <Pencil size={15} />
                        </Link>
                        <button
                          onClick={() => handleDelete(product.id, product.name)}
                          disabled={deleteProduct.isPending}
                          className="p-1.5 text-zinc-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                          title="Delete"
                        >
                          <Trash2 size={15} />
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

      <PaginationControls
        page={page}
        hasPrev={skip > 0}
        hasNext={!!products && products.length === limit}
        onPrev={prevPage}
        onNext={nextPage}
      />
    </div>
  )
}
