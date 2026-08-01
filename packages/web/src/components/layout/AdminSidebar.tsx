import { NavLink, Link } from "react-router-dom"
import {
  LayoutDashboard, Package, Tag, FolderOpen,
  ShoppingBag, RotateCcw, Ticket, Users, BarChart2, ArrowLeft
} from "lucide-react"
import { cn } from "@/lib/utils"

const links = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/products", label: "Products", icon: Package },
  { to: "/admin/categories", label: "Categories", icon: FolderOpen },
  { to: "/admin/tags", label: "Tags", icon: Tag },
  { to: "/admin/orders", label: "Orders", icon: ShoppingBag },
  { to: "/admin/returns", label: "Returns", icon: RotateCcw },
  { to: "/admin/coupons", label: "Coupons", icon: Ticket },
  { to: "/admin/users", label: "Users", icon: Users },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart2 },
]

export default function AdminSidebar() {
  return (
    <aside className="w-64 shrink-0 min-h-screen bg-charcoal text-sage flex flex-col">
      <div className="px-5 py-5 border-b border-sage/20">
        <span className="text-white font-black text-lg tracking-tight">Admin Panel</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-nested text-sm font-bold transition-colors",
                isActive
                  ? "bg-cream text-charcoal"
                  : "text-sage hover:bg-white/5 hover:text-white"
              )
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-3 py-4 border-t border-sage/20">
        <Link to="/" className="flex items-center gap-3 px-3 py-2 rounded-nested text-sm font-bold text-sage hover:bg-white/5 hover:text-white transition-colors">
          <ArrowLeft size={17} />
          Back to store
        </Link>
      </div>
    </aside>
  )
}
