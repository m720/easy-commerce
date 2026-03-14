import { Link, useNavigate } from "react-router-dom"
import { Trash2, Plus, Minus, ShoppingBag } from "lucide-react"
import { useCart, useUpdateCartItem, useRemoveCartItem } from "@/api/cart"
import { formatPrice } from "@/lib/utils"

export default function CartPage() {
  const { data: cart, isLoading } = useCart()
  const updateItem = useUpdateCartItem()
  const removeItem = useRemoveCartItem()
  const navigate = useNavigate()

  if (isLoading) return <div className="max-w-4xl mx-auto px-4 py-8 animate-pulse space-y-4">
    {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl" />)}
  </div>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingBag size={48} className="mx-auto text-gray-300 mb-4" />
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Your cart is empty</h2>
        <p className="text-gray-500 mb-6">Add some products to get started</p>
        <Link to="/products" className="bg-blue-600 text-white px-8 py-3 rounded-xl font-medium hover:bg-blue-700">
          Browse Products
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Shopping Cart ({cart.items.length})</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div key={item.id} className="bg-white border rounded-xl p-4 flex gap-4">
              <div className="w-20 h-20 bg-gray-100 rounded-lg flex-none" />
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 truncate">{item.variant.name}</h3>
                <p className="text-sm text-gray-500">{formatPrice(item.variant.price)} each</p>
                {!item.in_stock && (
                  <span className="text-xs text-red-600 font-medium">Out of stock</span>
                )}
                <div className="flex items-center gap-3 mt-3">
                  <button
                    onClick={() => updateItem.mutate({ itemId: item.id, quantity: item.quantity - 1 })}
                    disabled={item.quantity <= 1}
                    className="w-7 h-7 rounded-full border flex items-center justify-center hover:bg-gray-100 disabled:opacity-40"
                  >
                    <Minus size={12} />
                  </button>
                  <span className="text-sm font-medium w-6 text-center">{item.quantity}</span>
                  <button
                    onClick={() => updateItem.mutate({ itemId: item.id, quantity: item.quantity + 1 })}
                    className="w-7 h-7 rounded-full border flex items-center justify-center hover:bg-gray-100"
                  >
                    <Plus size={12} />
                  </button>
                </div>
              </div>
              <div className="flex flex-col items-end justify-between">
                <span className="font-semibold">{formatPrice(parseFloat(item.variant.price) * item.quantity)}</span>
                <button
                  onClick={() => removeItem.mutate(item.id)}
                  className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white border rounded-xl p-6 sticky top-24">
            <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span>{formatPrice(cart.subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
              <div className="border-t pt-2 mt-2 flex justify-between font-semibold">
                <span>Total</span>
                <span>{formatPrice(cart.subtotal)}</span>
              </div>
            </div>
            <button
              onClick={() => navigate("/checkout")}
              className="w-full mt-6 bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              Proceed to Checkout
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
