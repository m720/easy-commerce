import { Link } from "react-router-dom"
import { Package } from "lucide-react"
import { useOrders } from "@/api/orders"
import { usePagination } from "@/hooks/usePagination"
import { formatPrice, formatDate } from "@/lib/utils"
import OrderStatusBadge from "@/components/shared/OrderStatusBadge"
import PaginationControls from "@/components/shared/PaginationControls"

export default function OrdersPage() {
  const { skip, limit, page, nextPage, prevPage } = usePagination(10)
  const { data: orders, isLoading } = useOrders({ skip, limit })

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-charcoal mb-8">My Orders</h1>

      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="h-24 bg-sage/20 rounded-xl animate-pulse" />)}
        </div>
      ) : orders?.length === 0 ? (
        <div className="text-center py-16">
          <Package size={48} className="mx-auto text-sage mb-4" />
          <h2 className="text-lg font-medium text-charcoal/80 mb-2">No orders yet</h2>
          <Link to="/products" className="text-brand hover:underline text-sm">Start shopping</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders?.map((order) => (
            <Link
              key={order.id}
              to={`/orders/${order.id}`}
              className="block bg-white border border-sage/30 rounded-card shadow-soft p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm text-charcoal/70">Order #{order.id.slice(0, 8)}</p>
                  <p className="text-xs text-charcoal/70">{formatDate(order.created_at)}</p>
                </div>
                <OrderStatusBadge status={order.status} />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-charcoal/70">{order.items.length} item(s)</p>
                <p className="font-semibold">{formatPrice(order.total_amount)}</p>
              </div>
            </Link>
          ))}
        </div>
      )}

      <PaginationControls
        page={page}
        onPrev={prevPage}
        onNext={nextPage}
        hasPrev={page > 1}
        hasNext={(orders?.length ?? 0) === limit}
      />
    </div>
  )
}
