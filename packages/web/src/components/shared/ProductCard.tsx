import { Link } from "react-router-dom"
import { Heart } from "lucide-react"
import type { Product } from "@/types"
import { formatPrice } from "@/lib/utils"
import { useAddToWishlist, useWishlist } from "@/api/wishlist"
import { useAuthStore } from "@/store/authStore"

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  const { token } = useAuthStore()
  const { data: wishlist } = useWishlist()
  const addToWishlist = useAddToWishlist()

  const primaryImage = product.images.find((i) => i.is_primary) ?? product.images[0]
  const inWishlist = wishlist?.items.some((i) => i.product_id === product.id)

  return (
    <div className="bg-white rounded-2xl border border-zinc-200 overflow-hidden hover:shadow-lg hover:shadow-zinc-900/5 hover:-translate-y-0.5 transition-all duration-300 group">
      <Link to={`/products/${product.id}`} className="block relative">
        <div className="aspect-square bg-zinc-100 overflow-hidden">
          {primaryImage?.url ? (
            <img
              src={primaryImage.url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-zinc-400 text-sm">No image</div>
          )}
        </div>
        {product.is_featured && (
          <span className="absolute top-2.5 left-2.5 bg-zinc-900 text-white text-[11px] font-semibold px-2.5 py-1 rounded-full">Featured</span>
        )}
        {!product.is_active && (
          <span className="absolute top-2.5 right-2.5 bg-zinc-500 text-white text-[11px] font-semibold px-2.5 py-1 rounded-full">Inactive</span>
        )}
        {token && (
          <button
            onClick={(e) => { e.preventDefault(); addToWishlist.mutate(product.id) }}
            className={`absolute bottom-2.5 right-2.5 p-2 rounded-full shadow-sm transition-colors ${inWishlist ? "text-red-500 bg-white" : "text-zinc-500 bg-white/90 hover:text-red-500"}`}
            disabled={addToWishlist.isPending}
          >
            <Heart size={15} fill={inWishlist ? "currentColor" : "none"} />
          </button>
        )}
      </Link>

      <div className="p-4">
        <Link to={`/products/${product.id}`}>
          <h3 className="text-sm font-medium text-zinc-900 truncate hover:text-indigo-600 transition-colors">{product.name}</h3>
        </Link>
        {product.category && (
          <p className="text-xs text-zinc-500 mt-0.5">{product.category.name}</p>
        )}
        <p className="font-bold text-zinc-900 mt-2">{formatPrice(product.base_price)}</p>
      </div>
    </div>
  )
}
