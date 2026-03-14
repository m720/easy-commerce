import { useQuery } from "@tanstack/react-query"
import api from "./client"
import type { AnalyticsSummary, OrderStatusStat, TopProductStat, TopVariantStat, UserStat, AovStat, CouponStat, LowStockItem, UserActivitySummary, UUID } from "@/types"

interface DateRange { from_date?: string; to_date?: string }

export const useAnalyticsSummary = () =>
  useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => api.get<AnalyticsSummary>("/analytics/summary").then((r) => r.data),
  })

export const useAnalyticsRevenue = (params?: DateRange) =>
  useQuery({
    queryKey: ["analytics", "revenue", params],
    queryFn: () => api.get<{ total_revenue: number }>("/analytics/revenue", { params }).then((r) => r.data),
  })

export const useAnalyticsOrders = () =>
  useQuery({
    queryKey: ["analytics", "orders"],
    queryFn: () => api.get<OrderStatusStat[]>("/analytics/orders").then((r) => r.data),
  })

export const useAnalyticsTopProducts = (limit?: number) =>
  useQuery({
    queryKey: ["analytics", "top-products", limit],
    queryFn: () => api.get<TopProductStat[]>("/analytics/top-products", { params: { limit } }).then((r) => r.data),
  })

export const useAnalyticsTopVariants = (limit?: number) =>
  useQuery({
    queryKey: ["analytics", "top-variants", limit],
    queryFn: () => api.get<TopVariantStat[]>("/analytics/top-variants", { params: { limit } }).then((r) => r.data),
  })

export const useAnalyticsUsers = (params?: DateRange) =>
  useQuery({
    queryKey: ["analytics", "users", params],
    queryFn: () => api.get<UserStat>("/analytics/users", { params }).then((r) => r.data),
  })

export const useAnalyticsAov = () =>
  useQuery({
    queryKey: ["analytics", "aov"],
    queryFn: () => api.get<AovStat>("/analytics/aov").then((r) => r.data),
  })

export const useAnalyticsCoupons = () =>
  useQuery({
    queryKey: ["analytics", "coupons"],
    queryFn: () => api.get<CouponStat[]>("/analytics/coupons").then((r) => r.data),
  })

export const useAnalyticsLowStock = () =>
  useQuery({
    queryKey: ["analytics", "low-stock"],
    queryFn: () => api.get<LowStockItem[]>("/analytics/low-stock").then((r) => r.data),
  })

export const useUserActivity = (userId: UUID) =>
  useQuery({
    queryKey: ["users", userId, "activity"],
    queryFn: () => api.get<UserActivitySummary>(`/users/${userId}/activity`).then((r) => r.data),
    enabled: !!userId,
  })

export const downloadCsvReport = (report: "revenue" | "top-products" | "top-variants" | "coupons" | "low-stock") => {
  const token = localStorage.getItem("auth-storage")
  let authToken = ""
  if (token) {
    try {
      authToken = JSON.parse(token)?.state?.token ?? ""
    } catch {}
  }
  const link = document.createElement("a")
  link.href = `http://localhost:8000/api/v1/analytics/export/${report}.csv`
  link.setAttribute("download", `${report}.csv`)
  // For download, we need to use fetch with auth header
  fetch(`http://localhost:8000/api/v1/analytics/export/${report}.csv`, {
    headers: { Authorization: `Bearer ${authToken}` },
  })
    .then((r) => r.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      link.href = url
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    })
}
