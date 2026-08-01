import { useState } from "react"
import api from "@/api/client"
import { useAuthStore } from "@/store/authStore"
import type { User, TokenResponse } from "@/types"

const DEV_USERS = [
  { label: "Admin", email: "admin@example.com", password: "admin1234", role: "admin" },
  { label: "Alice (Customer)", email: "alice@example.com", password: "password123", role: "customer" },
  { label: "Bob (Customer)", email: "bob@example.com", password: "password123", role: "customer" },
]

export default function DevToolbar() {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState<string | null>(null)
  const { login, logout, user } = useAuthStore()

  if (!import.meta.env.DEV) return null

  async function loginAs(email: string, password: string) {
    setLoading(email)
    try {
      const tokenRes = await api.post<TokenResponse>("/auth/login", { email, password }).then((r) => r.data)
      const userRes = await api.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${tokenRes.access_token}` },
      }).then((r) => r.data)
      login(tokenRes.access_token, userRes)
      window.location.reload()
    } catch {
      // silently fail – dev tool
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="fixed bottom-4 left-4 z-[9999] flex flex-col items-start gap-2">
      {open && (
        <div className="mb-1 rounded-lg border border-zinc-200 bg-white shadow-xl w-56">
          <div className="px-3 py-2 border-b border-zinc-100 bg-zinc-50 rounded-t-lg">
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">Dev: Switch User</p>
            {user && (
              <p className="text-xs text-zinc-400 mt-0.5 truncate">Logged in: {user.email}</p>
            )}
          </div>
          <ul className="py-1">
            {DEV_USERS.map((u) => (
              <li key={u.email}>
                <button
                  onClick={() => loginAs(u.email, u.password)}
                  disabled={loading === u.email || user?.email === u.email}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${u.role === "admin" ? "bg-purple-500" : "bg-indigo-400"}`} />
                  <span className="flex-1 font-medium text-zinc-700">{u.label}</span>
                  {loading === u.email && (
                    <span className="text-xs text-zinc-400">...</span>
                  )}
                  {user?.email === u.email && (
                    <span className="text-xs text-green-500">✓</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
          {user && (
            <div className="border-t border-zinc-100 py-1">
              <button
                onClick={() => { logout(); window.location.reload() }}
                className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50 transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        title="Dev Tools"
        className="w-9 h-9 rounded-full bg-zinc-800 text-white flex items-center justify-center shadow-lg hover:bg-zinc-700 transition-colors border-2 border-zinc-600"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M6.28 5.22a.75.75 0 0 1 0 1.06L2.56 10l3.72 3.72a.75.75 0 0 1-1.06 1.06L.97 10.53a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0Zm7.44 0a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L17.44 10l-3.72-3.72a.75.75 0 0 1 0-1.06ZM11.377 2.011a.75.75 0 0 1 .612.867l-2.5 14.5a.75.75 0 0 1-1.478-.255l2.5-14.5a.75.75 0 0 1 .866-.612Z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  )
}
