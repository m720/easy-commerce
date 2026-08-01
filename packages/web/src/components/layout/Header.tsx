import { Link, NavLink, useNavigate } from "react-router-dom"
import { ShoppingCart, Heart, User, LogOut, LayoutDashboard, Menu, X, ShoppingBag } from "lucide-react"
import { useState } from "react"
import { useAuthStore } from "@/store/authStore"
import { useCart } from "@/api/cart"

export default function Header() {
  const { user, logout } = useAuthStore()
  const { data: cart } = useCart()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate("/")
  }

  const cartCount = cart?.items?.length ?? 0

  return (
    <header className="sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-zinc-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-zinc-900 text-white">
              <ShoppingBag size={16} strokeWidth={2.25} />
            </span>
            <span className="text-lg font-bold tracking-tight text-zinc-900">ShopApp</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            <NavLink to="/products" className={({ isActive }) => isActive ? "text-sm font-semibold text-zinc-900" : "text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"}>
              Products
            </NavLink>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-1">
            {user && (
              <>
                <Link to="/wishlist" className="p-2.5 rounded-full text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 transition-colors">
                  <Heart size={19} />
                </Link>
                <Link to="/cart" className="relative p-2.5 rounded-full text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 transition-colors">
                  <ShoppingCart size={19} />
                  {cartCount > 0 && (
                    <span className="absolute top-1 right-1 bg-indigo-600 text-white text-[10px] font-semibold rounded-full min-w-4 h-4 px-1 flex items-center justify-center">
                      {cartCount}
                    </span>
                  )}
                </Link>
              </>
            )}

            {user ? (
              <div className="relative group ml-1">
                <button className="flex items-center gap-2 text-sm text-zinc-700 hover:text-zinc-900 pl-2 pr-1 py-1.5 rounded-full hover:bg-zinc-100 transition-colors">
                  <span className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold flex items-center justify-center">
                    {user.full_name.charAt(0).toUpperCase()}
                  </span>
                  <span className="hidden md:block font-medium">{user.full_name.split(" ")[0]}</span>
                </button>
                <div className="absolute right-0 mt-1 w-52 bg-white border border-zinc-200 rounded-xl shadow-lg shadow-zinc-900/5 py-1.5 opacity-0 invisible translate-y-1 group-hover:opacity-100 group-hover:visible group-hover:translate-y-0 transition-all z-50">
                  <Link to="/profile" className="flex items-center gap-2.5 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">
                    <User size={16} /> Profile
                  </Link>
                  <Link to="/orders" className="flex items-center gap-2.5 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">
                    <ShoppingBag size={16} /> Orders
                  </Link>
                  {user.role === "admin" && (
                    <Link to="/admin" className="flex items-center gap-2.5 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">
                      <LayoutDashboard size={16} /> Admin
                    </Link>
                  )}
                  <hr className="my-1.5 border-zinc-100" />
                  <button onClick={handleLogout} className="flex items-center gap-2.5 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                    <LogOut size={16} /> Logout
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 ml-2">
                <Link to="/login" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 px-3 py-2">Login</Link>
                <Link to="/register" className="text-sm font-medium bg-zinc-900 text-white px-4 py-2 rounded-full hover:bg-zinc-700 transition-colors">Sign Up</Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button className="md:hidden p-2.5 ml-1 rounded-full hover:bg-zinc-100" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {menuOpen && (
          <div className="md:hidden py-3 border-t border-zinc-100">
            <NavLink to="/products" className="block py-2 text-sm font-medium text-zinc-700" onClick={() => setMenuOpen(false)}>
              Products
            </NavLink>
          </div>
        )}
      </div>
    </header>
  )
}
