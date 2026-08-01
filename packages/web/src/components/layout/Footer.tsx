import { Link } from "react-router-dom"
import { ShoppingBag } from "lucide-react"

export default function Footer() {
  return (
    <footer className="bg-charcoal text-sage mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-nested bg-white text-charcoal">
                <ShoppingBag size={14} strokeWidth={2.25} />
              </span>
              <span className="text-white font-black tracking-tight">ShopApp</span>
            </div>
            <p className="text-sm max-w-xs leading-relaxed">Thoughtfully curated products, fast shipping, and support that actually helps.</p>
          </div>
          <div>
            <h4 className="text-white label-xs mb-4">Shop</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/products" className="hover:text-white transition-colors">All Products</Link></li>
              <li><Link to="/cart" className="hover:text-white transition-colors">Cart</Link></li>
              <li><Link to="/orders" className="hover:text-white transition-colors">My Orders</Link></li>
              <li><Link to="/wishlist" className="hover:text-white transition-colors">Wishlist</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white label-xs mb-4">Account</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/login" className="hover:text-white transition-colors">Login</Link></li>
              <li><Link to="/register" className="hover:text-white transition-colors">Register</Link></li>
              <li><Link to="/profile" className="hover:text-white transition-colors">Profile</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-sage/20 mt-10 pt-6 text-center text-xs text-sage/70">
          © {new Date().getFullYear()} ShopApp. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
