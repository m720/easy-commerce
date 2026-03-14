import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api from "./client"
import { useAuthStore } from "@/store/authStore"
import type { User, TokenResponse } from "@/types"

export const useMe = () =>
  useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/auth/me").then((r) => r.data),
    enabled: !!useAuthStore.getState().token,
  })

export const useLogin = () => {
  const { login } = useAuthStore()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post<TokenResponse>("/auth/login", data).then((r) => r.data),
    onSuccess: async (tokenRes) => {
      const user = await api.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${tokenRes.access_token}` },
      }).then((r) => r.data)
      login(tokenRes.access_token, user)
      qc.invalidateQueries({ queryKey: ["me"] })
    },
  })
}

export const useRegister = () =>
  useMutation({
    mutationFn: (data: { email: string; full_name: string; password: string }) =>
      api.post<User>("/auth/register", data).then((r) => r.data),
  })

export const useUpdateMe = () => {
  const { setUser } = useAuthStore()
  return useMutation({
    mutationFn: (data: { full_name?: string; email?: string }) =>
      api.put<User>("/auth/me", data).then((r) => r.data),
    onSuccess: (user) => setUser(user),
  })
}

export const useChangePassword = () =>
  useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.put("/auth/me/password", data),
  })
