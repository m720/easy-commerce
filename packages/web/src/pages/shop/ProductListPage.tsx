import { useSearchParams } from "react-router-dom"
import { useState, useEffect } from "react"
import { Search, SlidersHorizontal, X } from "lucide-react"
import { useProducts } from "@/api/products"
import { useCategories } from "@/api/categories"
import { useTags } from "@/api/tags"
import { usePagination } from "@/hooks/usePagination"
import ProductCard from "@/components/shared/ProductCard"
import PaginationControls from "@/components/shared/PaginationControls"

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { skip, limit, page, nextPage, prevPage, reset } = usePagination(20)

  const [search, setSearch] = useState(searchParams.get("search") ?? "")
  const [categoryId, setCategoryId] = useState(searchParams.get("category_id") ? Number(searchParams.get("category_id")) : undefined)
  const [tagId, setTagId] = useState(searchParams.get("tag_id") ? Number(searchParams.get("tag_id")) : undefined)
  const [minPrice, setMinPrice] = useState(searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined)
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined)
  const [showFilters, setShowFilters] = useState(false)

  const { data: categories } = useCategories()
  const { data: tags } = useTags()

  const params = {
    search: search || undefined,
    category_id: categoryId,
    tag_id: tagId,
    min_price: minPrice,
    max_price: maxPrice,
    skip,
    limit,
  }

  const { data: products, isLoading } = useProducts(params)

  // Sync URL with filters
  useEffect(() => {
    const p: Record<string, string> = {}
    if (search) p.search = search
    if (categoryId) p.category_id = String(categoryId)
    if (tagId) p.tag_id = String(tagId)
    if (minPrice) p.min_price = String(minPrice)
    if (maxPrice) p.max_price = String(maxPrice)
    setSearchParams(p, { replace: true })
  }, [search, categoryId, tagId, minPrice, maxPrice, setSearchParams])

  const clearFilters = () => {
    setSearch("")
    setCategoryId(undefined)
    setTagId(undefined)
    setMinPrice(undefined)
    setMaxPrice(undefined)
    reset()
  }

  const hasFilters = search || categoryId || tagId || minPrice || maxPrice

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-zinc-900">All Products</h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm text-zinc-600 hover:text-zinc-900 border rounded-lg px-3 py-1.5"
        >
          <SlidersHorizontal size={16} />
          Filters
          {hasFilters && <span className="bg-zinc-900 text-white rounded-full text-xs w-4 h-4 flex items-center justify-center">!</span>}
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); reset() }}
          placeholder="Search products..."
          className="w-full pl-10 pr-4 py-2.5 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {search && (
          <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm shadow-zinc-900/5 p-4 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Category</label>
            <select
              value={categoryId ?? ""}
              onChange={(e) => { setCategoryId(e.target.value ? Number(e.target.value) : undefined); reset() }}
              className="w-full border rounded-lg px-2 py-1.5 text-sm"
            >
              <option value="">All categories</option>
              {categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Tag</label>
            <select
              value={tagId ?? ""}
              onChange={(e) => { setTagId(e.target.value ? Number(e.target.value) : undefined); reset() }}
              className="w-full border rounded-lg px-2 py-1.5 text-sm"
            >
              <option value="">All tags</option>
              {tags?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Min Price</label>
            <input
              type="number"
              value={minPrice ?? ""}
              onChange={(e) => { setMinPrice(e.target.value ? Number(e.target.value) : undefined); reset() }}
              className="w-full border rounded-lg px-2 py-1.5 text-sm"
              placeholder="$0"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Max Price</label>
            <input
              type="number"
              value={maxPrice ?? ""}
              onChange={(e) => { setMaxPrice(e.target.value ? Number(e.target.value) : undefined); reset() }}
              className="w-full border rounded-lg px-2 py-1.5 text-sm"
              placeholder="No limit"
            />
          </div>
          {hasFilters && (
            <button onClick={clearFilters} className="col-span-2 md:col-span-4 text-sm text-red-600 hover:underline text-left">
              Clear all filters
            </button>
          )}
        </div>
      )}

      {/* Product Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-zinc-100 rounded-xl aspect-square animate-pulse" />
          ))}
        </div>
      ) : products?.length === 0 ? (
        <div className="text-center py-16 text-zinc-500">
          <p className="text-lg">No products found</p>
          {hasFilters && <button onClick={clearFilters} className="mt-2 text-indigo-600 hover:underline text-sm">Clear filters</button>}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products?.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}

      <PaginationControls
        page={page}
        onPrev={prevPage}
        onNext={nextPage}
        hasPrev={page > 1}
        hasNext={(products?.length ?? 0) === limit}
      />
    </div>
  )
}
