import { Link } from "react-router-dom"
import { ArrowRight, Truck, RotateCcw, ShieldCheck } from "lucide-react"
import { useFeaturedProducts } from "@/api/products"
import { useCategories } from "@/api/categories"
import ProductCard from "@/components/shared/ProductCard"

const perks = [
  { icon: Truck, label: "Free shipping", detail: "On orders over $50" },
  { icon: RotateCcw, label: "Easy returns", detail: "30-day return window" },
  { icon: ShieldCheck, label: "Secure checkout", detail: "Your data stays protected" },
]

export default function HomePage() {
  const { data: featured, isLoading } = useFeaturedProducts({ limit: 8 })
  const { data: categories } = useCategories()

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-zinc-950 text-white">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[640px] h-[640px] rounded-full bg-indigo-600/25 blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto text-center px-4 py-28 sm:py-32">
          <span className="inline-block text-xs font-semibold tracking-wider text-indigo-300 uppercase mb-5">New season, new arrivals</span>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-5">Shop the best,<br />skip the rest</h1>
          <p className="text-lg text-zinc-400 mb-9 max-w-xl mx-auto">Thousands of quality products, curated for you and shipped fast.</p>
          <Link
            to="/products"
            className="inline-flex items-center gap-2 bg-white text-zinc-900 px-7 py-3.5 rounded-full font-semibold hover:bg-zinc-200 transition-colors"
          >
            Shop Now <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Trust strip */}
      <section className="border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
          {perks.map((perk) => (
            <div key={perk.label} className="flex items-center gap-3">
              <span className="flex items-center justify-center w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 shrink-0">
                <perk.icon size={18} />
              </span>
              <div>
                <p className="text-sm font-semibold text-zinc-900">{perk.label}</p>
                <p className="text-xs text-zinc-500">{perk.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900 mb-6">Shop by Category</h2>
          <div className="flex flex-wrap gap-3">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                to={`/products?category_id=${cat.id}`}
                className="px-5 py-2.5 bg-white border border-zinc-200 rounded-full text-sm font-medium text-zinc-700 hover:bg-zinc-900 hover:border-zinc-900 hover:text-white transition-colors"
              >
                {cat.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900">Featured Products</h2>
          <Link to="/products?is_featured=true" className="text-indigo-600 text-sm font-medium hover:underline flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-zinc-100 rounded-2xl aspect-square animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {featured?.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
