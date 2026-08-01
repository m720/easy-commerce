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
    <div className="bg-cream">
      {/* Hero */}
      <section className="px-4 sm:px-6 lg:px-8 pt-4">
        <div className="relative overflow-hidden bg-charcoal text-white rounded-card max-w-7xl mx-auto">
          {/* Decorative blob */}
          <div className="pointer-events-none absolute -top-24 -right-24 w-96 h-96 rounded-full bg-sage/20 blur-3xl" />
          <div className="relative text-center px-6 py-24 sm:py-28 max-w-3xl mx-auto">
            <span className="label-xs text-sage block mb-5">New season, new arrivals</span>
            <h1 className="text-4xl sm:text-6xl font-black tracking-tight mb-5">Shop the best,<br />skip the rest</h1>
            <p className="text-lg text-sage mb-9 max-w-xl mx-auto">Thoughtfully curated products, shipped fast.</p>
            <Link
              to="/products"
              className="inline-flex items-center gap-2 bg-brand text-white px-8 py-4 rounded-full font-black hover:bg-brand/90 transition-colors shadow-lg shadow-brand/30"
            >
              Shop Now <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Trust strip */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {perks.map((perk) => (
            <div key={perk.label} className="flex items-center gap-3 bg-white/80 backdrop-blur border border-sage/30 rounded-nested p-3">
              <span className="flex items-center justify-center w-10 h-10 rounded-full bg-brand/10 text-brand shrink-0">
                <perk.icon size={18} />
              </span>
              <div>
                <p className="text-sm font-black text-charcoal">{perk.label}</p>
                <p className="text-xs text-charcoal/70">{perk.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
          <h2 className="text-[32px] leading-tight font-black tracking-tight text-charcoal mb-6">Shop by Category</h2>
          <div className="flex flex-wrap gap-3">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                to={`/products?category_id=${cat.id}`}
                className="px-5 py-2.5 bg-white border border-sage/30 rounded-full text-sm font-bold text-charcoal/80 hover:bg-charcoal hover:border-charcoal hover:text-white transition-colors"
              >
                {cat.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-[32px] leading-tight font-black tracking-tight text-charcoal">Featured Products</h2>
          <Link to="/products?is_featured=true" className="text-brand text-sm font-bold hover:underline flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-sage/20 rounded-card aspect-square animate-pulse" />
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
