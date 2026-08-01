import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ShoppingCart, Heart, ArrowLeft } from "lucide-react"
import { useProduct } from "@/api/products"
import { useProductReviews, useCreateReview } from "@/api/reviews"
import { useAddToCart } from "@/api/cart"
import { useAddToWishlist } from "@/api/wishlist"
import { useAuthStore } from "@/store/authStore"
import { formatPrice, formatDate } from "@/lib/utils"
import ReviewStars from "@/components/shared/ReviewStars"
import type { ProductVariant } from "@/types"

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const { data: product, isLoading } = useProduct(id!)
  const { data: reviews } = useProductReviews(id!)
  const addToCart = useAddToCart()
  const addToWishlist = useAddToWishlist()
  const createReview = useCreateReview(id!)

  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null)
  const [activeImage, setActiveImage] = useState(0)
  const [reviewRating, setReviewRating] = useState(5)
  const [reviewComment, setReviewComment] = useState("")

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="animate-pulse grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="aspect-square bg-sage/30 rounded-xl" />
          <div className="space-y-4">
            <div className="h-8 bg-sage/30 rounded w-3/4" />
            <div className="h-4 bg-sage/30 rounded w-1/2" />
          </div>
        </div>
      </div>
    )
  }

  if (!product) return <div className="text-center py-16">Product not found</div>

  const variant = selectedVariant ?? product.variants[0] ?? null
  const price = variant ? variant.price : product.base_price
  const primaryImage = product.images.find((i) => i.is_primary) ?? product.images[0]
  const images = product.images.length > 0 ? product.images : []

  const handleAddToCart = () => {
    if (!token) { navigate("/login"); return }
    if (!variant) return
    addToCart.mutate({ variant_id: variant.id, quantity: 1 })
  }

  const handleSubmitReview = (e: React.FormEvent) => {
    e.preventDefault()
    createReview.mutate({ rating: reviewRating, comment: reviewComment }, {
      onSuccess: () => { setReviewComment("") }
    })
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-charcoal/70 hover:text-charcoal/80 mb-6">
        <ArrowLeft size={16} /> Back
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {/* Images */}
        <div>
          <div className="aspect-square bg-sage/20 rounded-xl overflow-hidden mb-3">
            {images[activeImage]?.url ? (
              <img src={images[activeImage].url!} alt={product.name} className="w-full h-full object-cover" />
            ) : primaryImage?.url ? (
              <img src={primaryImage.url} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-charcoal/70">No image</div>
            )}
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(i)}
                  className={`flex-none w-16 h-16 rounded-lg overflow-hidden border-2 ${i === activeImage ? "border-brand" : "border-transparent"}`}
                >
                  {img.url && <img src={img.url} alt="" className="w-full h-full object-cover" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="space-y-4">
          <div>
            {product.category && <p className="text-sm text-brand font-medium">{product.category.name}</p>}
            <h1 className="text-3xl font-bold text-charcoal mt-1">{product.name}</h1>
          </div>

          <div className="text-3xl font-bold text-charcoal">{formatPrice(price)}</div>

          {product.description && (
            <p className="text-charcoal/70 leading-relaxed">{product.description}</p>
          )}

          {/* Tags */}
          {product.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {product.tags.map((tag) => (
                <span key={tag.id} className="text-xs bg-sage/20 text-charcoal/70 px-2.5 py-1 rounded-full">{tag.name}</span>
              ))}
            </div>
          )}

          {/* Variants */}
          {product.variants.length > 0 && (
            <div>
              <p className="text-sm font-medium text-charcoal/80 mb-2">Select variant:</p>
              <div className="flex flex-wrap gap-2">
                {product.variants.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => setSelectedVariant(v)}
                    disabled={v.stock_quantity === 0}
                    className={`px-4 py-2 border rounded-lg text-sm transition-all ${
                      variant?.id === v.id
                        ? "border-brand bg-brand/10 text-brand"
                        : v.stock_quantity === 0
                        ? "border-sage/30 text-sage cursor-not-allowed"
                        : "border-sage/30 hover:border-sage"
                    }`}
                  >
                    {v.name}
                    {v.stock_quantity === 0 && " (Out of stock)"}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleAddToCart}
              disabled={addToCart.isPending || (variant !== null && variant.stock_quantity === 0)}
              className="flex-1 flex items-center justify-center gap-2 bg-brand text-white py-3 rounded-xl font-medium hover:bg-brand/90 disabled:opacity-50 transition-colors"
            >
              <ShoppingCart size={18} />
              {addToCart.isPending ? "Adding..." : "Add to Cart"}
            </button>
            {token && (
              <button
                onClick={() => addToWishlist.mutate(product.id)}
                className="p-3 border rounded-xl hover:bg-red-50 hover:border-red-200 transition-colors"
              >
                <Heart size={20} className="text-charcoal/70" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Reviews */}
      <div className="mt-16">
        <h2 className="text-xl font-bold text-charcoal mb-6">
          Reviews ({reviews?.length ?? 0})
        </h2>

        {token && (
          <form onSubmit={handleSubmitReview} className="bg-white border border-sage/30 rounded-card shadow-soft p-6 mb-8">
            <h3 className="font-medium text-charcoal mb-4">Write a review</h3>
            <div className="mb-4">
              <p className="text-sm text-charcoal/80 mb-2">Rating</p>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setReviewRating(r)}
                    className={`text-2xl transition-colors ${r <= reviewRating ? "text-yellow-400" : "text-sage"}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              placeholder="Share your thoughts..."
              rows={3}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand resize-none"
            />
            <button
              type="submit"
              disabled={createReview.isPending}
              className="mt-3 bg-brand text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-brand/90 disabled:opacity-60"
            >
              {createReview.isPending ? "Submitting..." : "Submit Review"}
            </button>
          </form>
        )}

        <div className="space-y-4">
          {reviews?.map((review) => (
            <div key={review.id} className="bg-white border border-sage/30 rounded-card shadow-soft p-5">
              <div className="flex items-center gap-3 mb-2">
                <ReviewStars rating={review.rating} />
                <span className="text-xs text-charcoal/70">{formatDate(review.created_at)}</span>
              </div>
              {review.comment && <p className="text-charcoal/80 text-sm">{review.comment}</p>}
            </div>
          ))}
          {reviews?.length === 0 && (
            <p className="text-charcoal/70 text-sm">No reviews yet. Be the first to review!</p>
          )}
        </div>
      </div>
    </div>
  )
}
