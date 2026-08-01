import { Outlet } from "react-router-dom"
import AdminSidebar from "./AdminSidebar"

export default function AdminLayout() {
  return (
    <div className="flex min-h-screen bg-cream">
      <AdminSidebar />
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  )
}
