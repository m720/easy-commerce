import { Link, NavLink, useNavigate } from "react-router-dom"
import { ShoppingCart, Heart, User, LogOut, LayoutDashboard, Menu, X } from "lucide-react"
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
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="text-xl font-bold text-blue-600">
            ShopApp
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            <NavLink to="/products" className={({ isActive }) => isActive ? "text-blue-600 font-medium" : "text-gray-600 hover:text-gray-900"}>
              Products
            </NavLink>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {user && (
              <>
                <Link to="/wishlist" className="p-2 text-gray-600 hover:text-gray-900">
                  <Heart size={20} />
                </Link>
                <Link to="/cart" className="relative p-2 text-gray-600 hover:text-gray-900">
                  <ShoppingCart size={20} />
                  {cartCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {cartCount}
                    </span>
                  )}
                </Link>
              </>
            )}

            {user ? (
              <div className="relative group">
                <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 p-2">
                  <User size={20} />
                  <span className="hidden md:block">{user.full_name.split(" ")[0]}</span>
                </button>
                <div className="absolute right-0 mt-1 w-48 bg-white border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                  <Link to="/profile" className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50">
                    <User size={16} /> Profile
                  </Link>
                  <Link to="/orders" className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50">
                    Orders
                  </Link>
                  {user.role === "admin" && (
                    <Link to="/admin" className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50">
                      <LayoutDashboard size={16} /> Admin
                    </Link>
                  )}
                  <hr className="my-1" />
                  <button onClick={handleLogout} className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-gray-50">
                    <LogOut size={16} /> Logout
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5">Login</Link>
                <Link to="/register" className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700">Sign Up</Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button className="md:hidden p-2" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {menuOpen && (
          <div className="md:hidden py-3 border-t">
            <NavLink to="/products" className="block py-2 text-gray-700" onClick={() => setMenuOpen(false)}>
              Products
            </NavLink>
          </div>
        )}
      </div>
    </header>
  )
}
