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
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group">
      <Link to={`/products/${product.id}`} className="block relative">
        <div className="aspect-square bg-gray-100 overflow-hidden">
          {primaryImage?.url ? (
            <img
              src={primaryImage.url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">No image</div>
          )}
        </div>
        {product.is_featured && (
          <span className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">Featured</span>
        )}
        {!product.is_active && (
          <span className="absolute top-2 right-2 bg-gray-500 text-white text-xs px-2 py-0.5 rounded-full">Inactive</span>
        )}
      </Link>

      <div className="p-4">
        <Link to={`/products/${product.id}`}>
          <h3 className="font-medium text-gray-900 truncate hover:text-blue-600">{product.name}</h3>
        </Link>
        {product.category && (
          <p className="text-xs text-gray-500 mt-0.5">{product.category.name}</p>
        )}
        <div className="flex items-center justify-between mt-3">
          <span className="font-bold text-gray-900">{formatPrice(product.base_price)}</span>
          {token && (
            <button
              onClick={() => addToWishlist.mutate(product.id)}
              className={`p-1.5 rounded-full transition-colors ${inWishlist ? "text-red-500 bg-red-50" : "text-gray-400 hover:text-red-500 hover:bg-red-50"}`}
              disabled={addToWishlist.isPending}
            >
              <Heart size={16} fill={inWishlist ? "currentColor" : "none"} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
