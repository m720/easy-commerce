import { Navigate, useLocation } from "react-router-dom"
import { useAuthStore } from "@/store/authStore"
import type { UserRole } from "@/types"

interface AuthGuardProps {
  children: React.ReactNode
  role?: UserRole
}

export default function AuthGuard({ children, role }: AuthGuardProps) {
  const { user, token } = useAuthStore()
  const location = useLocation()

  if (!token || !user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />
  }

  if (role === "admin" && user.role !== "admin") {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
