import { useState } from "react"
import { Download, TrendingUp, ShoppingBag, Users, DollarSign, AlertTriangle } from "lucide-react"
import {
  useAnalyticsSummary,
  useAnalyticsRevenue,
  useAnalyticsOrders,
  useAnalyticsTopProducts,
  useAnalyticsTopVariants,
  useAnalyticsUsers,
  useAnalyticsAov,
  useAnalyticsCoupons,
  useAnalyticsLowStock,
  downloadCsvReport,
} from "@/api/analytics"
import { formatPrice, formatDate } from "@/lib/utils"

export default function AnalyticsPage() {
  const [fromDate, setFromDate] = useState("")
  const [toDate, setToDate] = useState("")

  const dateRange = {
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  }

  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary()
  const { data: revenue, isLoading: revenueLoading } = useAnalyticsRevenue(dateRange)
  const { data: orders } = useAnalyticsOrders()
  const { data: topProducts } = useAnalyticsTopProducts(10)
  const { data: topVariants } = useAnalyticsTopVariants(10)
  const { data: users } = useAnalyticsUsers(dateRange)
  const { data: aov } = useAnalyticsAov()
  const { data: coupons } = useAnalyticsCoupons()
  const { data: lowStock, isLoading: lowStockLoading } = useAnalyticsLowStock()

  const totalOrders = summary?.orders_by_status?.reduce((sum, s) => sum + s.count, 0) ?? 0

  return (
    <div className="p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white border rounded-xl p-5">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Date Range Filter</h2>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">From</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">To</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          {(fromDate || toDate) && (
            <button
              onClick={() => { setFromDate(""); setToDate("") }}
              className="border px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          {
            label: "Total Revenue",
            value: revenueLoading ? null : formatPrice(revenue?.total_revenue ?? summary?.total_revenue ?? 0),
            icon: DollarSign,
            color: "text-green-600",
            bg: "bg-green-50",
          },
          {
            label: "Total Orders",
            value: summaryLoading ? null : totalOrders.toString(),
            icon: ShoppingBag,
            color: "text-blue-600",
            bg: "bg-blue-50",
          },
          {
            label: "Avg. Order Value",
            value: aov ? formatPrice(aov.average_order_value) : (summaryLoading ? null : formatPrice(summary?.average_order_value ?? 0)),
            icon: TrendingUp,
            color: "text-orange-600",
            bg: "bg-orange-50",
          },
          {
            label: "Total Users",
            value: users ? users.total_users.toString() : (summaryLoading ? null : (summary?.total_users ?? 0).toString()),
            icon: Users,
            color: "text-purple-600",
            bg: "bg-purple-50",
          },
          {
            label: "New Users",
            value: users ? users.new_users_in_period.toString() : (summaryLoading ? null : (summary?.new_users_in_period ?? 0).toString()),
            icon: Users,
            color: "text-indigo-600",
            bg: "bg-indigo-50",
          },
        ].map((card) => (
          <div key={card.label} className="bg-white border rounded-xl p-5 flex items-center gap-3">
            <div className={`${card.bg} p-2.5 rounded-lg shrink-0`}>
              <card.icon className={`${card.color} w-5 h-5`} />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-gray-500 truncate">{card.label}</p>
              {card.value === null ? (
                <div className="h-6 w-20 bg-gray-200 animate-pulse rounded mt-1" />
              ) : (
                <p className="text-lg font-bold text-gray-900">{card.value}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Orders by Status */}
      <div className="bg-white border rounded-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Orders by Status</h2>
        {!orders ? (
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 animate-pulse rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {orders.map((s) => (
              <div key={s.status} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-gray-900">{s.count}</p>
                <p className="text-xs text-gray-500 capitalize mt-1">{s.status}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Products */}
      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Top Products</h2>
          <button
            onClick={() => downloadCsvReport("top-products")}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
        {!topProducts ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : topProducts.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No product sales data yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Product</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Units Sold</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {topProducts.map((p, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="px-3 py-2 text-gray-900">{p.product_name}</td>
                    <td className="px-3 py-2 text-right text-gray-700">{p.total_sold}</td>
                    <td className="px-3 py-2 text-right font-semibold text-gray-900">
                      {formatPrice(p.total_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Top Variants */}
      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Top Variants</h2>
          <button
            onClick={() => downloadCsvReport("top-variants")}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
        {!topVariants ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : topVariants.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No variant sales data yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Variant</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Units Sold</th>
                </tr>
              </thead>
              <tbody>
                {topVariants.map((v, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="px-3 py-2 text-gray-900">{v.variant_name}</td>
                    <td className="px-3 py-2 text-right text-gray-700">{v.total_sold}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Coupons Usage */}
      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Coupon Usage</h2>
          <button
            onClick={() => downloadCsvReport("coupons")}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
        {!coupons ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : coupons.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No coupon usage data yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Code</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Used</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Max Uses</th>
                </tr>
              </thead>
              <tbody>
                {coupons.map((c, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="px-3 py-2">
                      <span className="font-mono font-semibold text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">
                        {c.code}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right text-gray-700">{c.used_count}</td>
                    <td className="px-3 py-2 text-right text-gray-600">{c.max_uses ?? "∞"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Low Stock */}
      <div className="bg-white border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-amber-500 w-5 h-5" />
            <h2 className="text-lg font-semibold text-gray-900">Low Stock</h2>
          </div>
          <button
            onClick={() => downloadCsvReport("low-stock")}
            className="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
        {lowStockLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !lowStock || lowStock.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No low stock items. Everything looks good!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">SKU</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Name</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">In Stock</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Threshold</th>
                </tr>
              </thead>
              <tbody>
                {lowStock.map((item) => (
                  <tr key={item.variant_id} className="border-b last:border-0">
                    <td className="px-3 py-2 font-mono text-xs text-gray-600">{item.sku}</td>
                    <td className="px-3 py-2 text-gray-900">{item.name}</td>
                    <td className="px-3 py-2 text-right font-semibold text-amber-600">{item.stock_quantity}</td>
                    <td className="px-3 py-2 text-right text-gray-500">{item.low_stock_threshold}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Revenue Export */}
      <div className="flex justify-end">
        <button
          onClick={() => downloadCsvReport("revenue")}
          className="inline-flex items-center gap-2 border px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
        >
          <Download size={15} /> Export Revenue CSV
        </button>
      </div>
    </div>
  )
}
