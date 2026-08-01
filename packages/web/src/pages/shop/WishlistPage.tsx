import { Link } from "react-router-dom"
import { Heart, ShoppingCart, Trash2 } from "lucide-react"
import { useWishlist, useRemoveFromWishlist, useMoveToCart } from "@/api/wishlist"
import { formatPrice } from "@/lib/utils"

export default function WishlistPage() {
  const { data: wishlist, isLoading } = useWishlist()
  const removeItem = useRemoveFromWishlist()
  const moveToCart = useMoveToCart()

  if (isLoading) return <div className="max-w-4xl mx-auto px-4 py-8 animate-pulse space-y-4">
    {[1,2,3].map(i => <div key={i} className="h-24 bg-zinc-100 rounded-xl" />)}
  </div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-zinc-900 mb-8">My Wishlist</h1>

      {!wishlist?.items.length ? (
        <div className="text-center py-16">
          <Heart size={48} className="mx-auto text-zinc-300 mb-4" />
          <h2 className="text-lg font-medium text-zinc-700 mb-2">Your wishlist is empty</h2>
          <Link to="/products" className="text-indigo-600 hover:underline text-sm">Browse products</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {wishlist.items.map((item) => {
            const product = item.product
            const primaryImage = product.images.find(i => i.is_primary) ?? product.images[0]
            return (
              <div key={item.id} className="bg-white border border-zinc-200 rounded-2xl shadow-sm shadow-zinc-900/5 p-4 flex gap-4">
                <Link to={`/products/${product.id}`} className="w-20 h-20 bg-zinc-100 rounded-lg overflow-hidden flex-none">
                  {primaryImage?.url && (
                    <img src={primaryImage.url} alt={product.name} className="w-full h-full object-cover" />
                  )}
                </Link>
                <div className="flex-1 min-w-0">
                  <Link to={`/products/${product.id}`} className="font-medium text-zinc-900 hover:text-indigo-600 truncate block">
                    {product.name}
                  </Link>
                  <p className="text-sm font-semibold text-zinc-900 mt-1">{formatPrice(product.base_price)}</p>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => moveToCart.mutate(item.id)}
                      disabled={moveToCart.isPending}
                      className="flex items-center gap-1 text-xs bg-zinc-900 text-white px-3 py-1.5 rounded-lg hover:bg-zinc-800 disabled:opacity-60"
                    >
                      <ShoppingCart size={12} /> Move to Cart
                    </button>
                    <button
                      onClick={() => removeItem.mutate(item.id)}
                      className="p-1.5 text-zinc-400 hover:text-red-500"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
