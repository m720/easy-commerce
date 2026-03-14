import { useState } from "react"
import { useAdminOrders, useUpdateOrderStatus } from "@/api/orders"
import { formatPrice, formatDate } from "@/lib/utils"
import { usePagination } from "@/hooks/usePagination"
import PaginationControls from "@/components/shared/PaginationControls"
import OrderStatusBadge from "@/components/shared/OrderStatusBadge"
import type { OrderStatus } from "@/types"

const ORDER_STATUSES: OrderStatus[] = ["pending", "processing", "shipped", "delivered", "cancelled", "returned"]

export default function AdminOrdersPage() {
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "">("")
  const { skip, limit, page, nextPage, prevPage, reset } = usePagination(20)

  const { data: orders, isLoading } = useAdminOrders({
    status: statusFilter || undefined,
    skip,
    limit,
  })
  const updateStatus = useUpdateOrderStatus()

  const handleStatusChange = (orderId: string, newStatus: OrderStatus) => {
    updateStatus.mutate({ id: orderId, status: newStatus })
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Filter by status:</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as OrderStatus | "")
              reset()
            }}
            className="border rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="">All Statuses</option>
            {ORDER_STATUSES.map((s) => (
              <option key={s} value={s} className="capitalize">
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white border rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !orders || orders.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="font-medium">No orders found</p>
            <p className="text-sm mt-1">
              {statusFilter ? `No orders with status "${statusFilter}".` : "No orders yet."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Order ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Customer</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Items</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Total</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Update Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                        {order.id.slice(0, 8)}…
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {formatDate(order.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {order.user_id ? (
                        <span className="font-mono text-xs text-gray-500">{order.user_id.slice(0, 8)}…</span>
                      ) : (
                        <span className="text-gray-400 text-xs">Guest</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700">
                      {order.items.length}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">
                      {formatPrice(order.total_amount)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={order.status}
                        onChange={(e) => handleStatusChange(order.id, e.target.value as OrderStatus)}
                        disabled={updateStatus.isPending}
                        className="border rounded px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 disabled:opacity-50"
                      >
                        {ORDER_STATUSES.map((s) => (
                          <option key={s} value={s} className="capitalize">
                            {s.charAt(0).toUpperCase() + s.slice(1)}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <PaginationControls
        page={page}
        hasPrev={skip > 0}
        hasNext={!!orders && orders.length === limit}
        onPrev={prevPage}
        onNext={nextPage}
      />
    </div>
  )
}
