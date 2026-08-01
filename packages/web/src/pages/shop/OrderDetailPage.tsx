import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { useOrder, useCancelOrder } from "@/api/orders"
import { useSubmitReturn } from "@/api/returns"
import { formatPrice, formatDate } from "@/lib/utils"
import OrderStatusBadge from "@/components/shared/OrderStatusBadge"

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: order, isLoading } = useOrder(id!)
  const cancelOrder = useCancelOrder()
  const submitReturn = useSubmitReturn(id!)

  const [showReturnForm, setShowReturnForm] = useState(false)
  const [returnReason, setReturnReason] = useState("")
  const [returnItems, setReturnItems] = useState<Record<string, number>>({})

  if (isLoading) return <div className="max-w-3xl mx-auto px-4 py-8 animate-pulse space-y-4">
    <div className="h-8 bg-sage/30 rounded w-1/3" />
    <div className="h-48 bg-sage/20 rounded-xl" />
  </div>

  if (!order) return <div className="text-center py-16">Order not found</div>

  const handleReturn = (e: React.FormEvent) => {
    e.preventDefault()
    const items = Object.entries(returnItems)
      .filter(([, qty]) => qty > 0)
      .map(([order_item_id, quantity]) => ({ order_item_id, quantity }))
    if (!items.length || !returnReason) return
    submitReturn.mutate({ reason: returnReason, items }, {
      onSuccess: () => setShowReturnForm(false),
    })
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <button onClick={() => navigate("/orders")} className="flex items-center gap-2 text-sm text-charcoal/70 hover:text-charcoal/80 mb-6">
        <ArrowLeft size={16} /> Back to Orders
      </button>

      <div className="bg-white border border-sage/30 rounded-card shadow-soft p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-charcoal">Order #{order.id.slice(0, 8)}</h1>
            <p className="text-sm text-charcoal/70 mt-1">Placed {formatDate(order.created_at)}</p>
          </div>
          <OrderStatusBadge status={order.status} />
        </div>

        {/* Items */}
        <div className="border-t pt-4 space-y-3">
          {order.items.map((item) => (
            <div key={item.id} className="flex justify-between items-start">
              <div>
                <p className="font-medium text-charcoal">{item.product_name}</p>
                <p className="text-sm text-charcoal/70">{item.variant_name} × {item.quantity}</p>
              </div>
              <span className="font-medium">{formatPrice(item.subtotal)}</span>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div className="border-t mt-4 pt-4 space-y-2 text-sm">
          {parseFloat(order.discount_amount) > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount</span>
              <span>-{formatPrice(order.discount_amount)}</span>
            </div>
          )}
          <div className="flex justify-between font-bold text-base">
            <span>Total</span>
            <span>{formatPrice(order.total_amount)}</span>
          </div>
        </div>

        {/* Shipping Address */}
        {order.shipping_address_snapshot && (
          <div className="border-t mt-4 pt-4">
            <p className="text-sm font-medium text-charcoal/80 mb-1">Shipping to:</p>
            <p className="text-sm text-charcoal/70">
              {order.shipping_address_snapshot.street}, {order.shipping_address_snapshot.city},{" "}
              {order.shipping_address_snapshot.country}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-6">
          {order.status === "pending" && (
            <button
              onClick={() => cancelOrder.mutate(order.id, { onSuccess: () => navigate("/orders") })}
              disabled={cancelOrder.isPending}
              className="px-4 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50 disabled:opacity-50"
            >
              Cancel Order
            </button>
          )}
          {order.status === "delivered" && (
            <button
              onClick={() => setShowReturnForm(!showReturnForm)}
              className="px-4 py-2 border rounded-lg text-sm hover:bg-cream"
            >
              Request Return
            </button>
          )}
        </div>
      </div>

      {/* Return Form */}
      {showReturnForm && (
        <div className="bg-white border border-sage/30 rounded-card shadow-soft p-6">
          <h2 className="font-semibold text-charcoal mb-4">Request Return</h2>
          <form onSubmit={handleReturn} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-charcoal/80 mb-1">Reason</label>
              <textarea
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                rows={3}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand resize-none"
                placeholder="Please describe the reason for return..."
              />
            </div>
            <div>
              <p className="text-sm font-medium text-charcoal/80 mb-2">Items to return:</p>
              {order.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <p className="text-sm">{item.product_name} — {item.variant_name}</p>
                    <p className="text-xs text-charcoal/70">Ordered: {item.quantity}</p>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={item.quantity}
                    value={returnItems[item.id] ?? 0}
                    onChange={(e) => setReturnItems({ ...returnItems, [item.id]: Number(e.target.value) })}
                    className="w-16 border rounded px-2 py-1 text-sm text-center"
                  />
                </div>
              ))}
            </div>
            <button
              type="submit"
              disabled={submitReturn.isPending}
              className="bg-brand text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-brand/90 disabled:opacity-60"
            >
              {submitReturn.isPending ? "Submitting..." : "Submit Return"}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
