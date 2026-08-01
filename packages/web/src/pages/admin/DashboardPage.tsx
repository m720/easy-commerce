import { TrendingUp, ShoppingBag, Users, DollarSign, AlertTriangle } from "lucide-react"
import { Link } from "react-router-dom"
import { useAnalyticsSummary, useAnalyticsLowStock } from "@/api/analytics"
import { formatPrice } from "@/lib/utils"

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary()
  const { data: lowStock, isLoading: lowStockLoading } = useAnalyticsLowStock()

  const totalOrders = summary?.orders_by_status?.reduce((sum, s) => sum + s.count, 0) ?? 0

  const statCards = [
    {
      label: "Total Revenue",
      value: summaryLoading ? null : formatPrice(summary?.total_revenue ?? 0),
      icon: DollarSign,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "Total Orders",
      value: summaryLoading ? null : totalOrders.toString(),
      icon: ShoppingBag,
      color: "text-brand",
      bg: "bg-brand/10",
    },
    {
      label: "Total Users",
      value: summaryLoading ? null : (summary?.total_users ?? 0).toString(),
      icon: Users,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      label: "Avg. Order Value",
      value: summaryLoading ? null : formatPrice(summary?.average_order_value ?? 0),
      icon: TrendingUp,
      color: "text-orange-600",
      bg: "bg-orange-50",
    },
  ]

  return (
    <div className="p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-charcoal">Dashboard</h1>
        <Link
          to="/admin/analytics"
          className="text-sm font-medium text-brand hover:text-brand hover:underline"
        >
          View Full Analytics →
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="bg-white border border-sage/30 rounded-nested shadow-soft p-5 flex items-center gap-4">
            <div className={`${card.bg} p-3 rounded-lg`}>
              <card.icon className={`${card.color} w-6 h-6`} />
            </div>
            <div>
              <p className="text-sm text-charcoal/70">{card.label}</p>
              {card.value === null ? (
                <div className="h-6 w-24 bg-sage/30 animate-pulse rounded mt-1" />
              ) : (
                <p className="text-xl font-bold text-charcoal">{card.value}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Orders by Status */}
      <div className="bg-white border border-sage/30 rounded-nested shadow-soft p-5">
        <h2 className="text-lg font-semibold text-charcoal mb-4">Orders by Status</h2>
        {summaryLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-16 bg-sage/20 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {summary?.orders_by_status?.map((s) => (
              <div key={s.status} className="bg-cream rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-charcoal">{s.count}</p>
                <p className="text-xs text-charcoal/70 capitalize mt-1">{s.status}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Low Stock Table */}
      <div className="bg-white border border-sage/30 rounded-nested shadow-soft p-5">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="text-amber-500 w-5 h-5" />
          <h2 className="text-lg font-semibold text-charcoal">Low Stock Alerts</h2>
        </div>
        {lowStockLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-sage/20 animate-pulse rounded" />
            ))}
          </div>
        ) : !lowStock || lowStock.length === 0 ? (
          <p className="text-sm text-charcoal/70 py-4 text-center">No low stock items. Everything looks good!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-charcoal/70">
                  <th className="pb-2 pr-4 font-medium">SKU</th>
                  <th className="pb-2 pr-4 font-medium">Name</th>
                  <th className="pb-2 pr-4 font-medium text-right">In Stock</th>
                  <th className="pb-2 font-medium text-right">Threshold</th>
                </tr>
              </thead>
              <tbody>
                {lowStock.map((item) => (
                  <tr key={item.variant_id} className="border-b last:border-0">
                    <td className="py-2 pr-4 font-mono text-xs text-charcoal/70">{item.sku}</td>
                    <td className="py-2 pr-4 text-charcoal">{item.name}</td>
                    <td className="py-2 pr-4 text-right font-semibold text-amber-600">{item.stock_quantity}</td>
                    <td className="py-2 text-right text-charcoal/70">{item.low_stock_threshold}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
