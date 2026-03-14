import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { CheckCircle } from "lucide-react"
import { useCart } from "@/api/cart"
import { useAddresses, useCreateAddress } from "@/api/addresses"
import { usePlaceOrder } from "@/api/orders"
import { formatPrice } from "@/lib/utils"
import CouponInput from "@/components/shared/CouponInput"
import type { CouponValidateResponse, UUID } from "@/types"

export default function CheckoutPage() {
  const navigate = useNavigate()
  const { data: cart } = useCart()
  const { data: addresses } = useAddresses()
  const placeOrder = usePlaceOrder()
  const createAddress = useCreateAddress()

  const [selectedAddressId, setSelectedAddressId] = useState<UUID>("")
  const [couponResult, setCouponResult] = useState<CouponValidateResponse | null>(null)
  const [showAddAddress, setShowAddAddress] = useState(false)
  const [newAddr, setNewAddr] = useState({ street: "", city: "", country: "", postal_code: "", state: "", label: "" })

  const subtotal = cart?.subtotal ?? "0"
  const discount = couponResult ? parseFloat(couponResult.discount_amount) : 0
  const total = Math.max(0, parseFloat(subtotal) - discount)

  const handleSubmit = () => {
    if (!selectedAddressId) return
    placeOrder.mutate({
      address_id: selectedAddressId,
      coupon_code: couponResult?.coupon.code,
    }, {
      onSuccess: (order) => navigate(`/orders/${order.id}`),
    })
  }

  const handleAddAddress = (e: React.FormEvent) => {
    e.preventDefault()
    createAddress.mutate(newAddr, {
      onSuccess: (addr) => {
        setSelectedAddressId(addr.id)
        setShowAddAddress(false)
      },
    })
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Checkout</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Address + Coupon */}
        <div className="lg:col-span-2 space-y-6">
          {/* Address Selection */}
          <div className="bg-white border rounded-xl p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Shipping Address</h2>
            {addresses && addresses.length > 0 ? (
              <div className="space-y-3">
                {addresses.map((addr) => (
                  <label
                    key={addr.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedAddressId === addr.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="address"
                      value={addr.id}
                      checked={selectedAddressId === addr.id}
                      onChange={() => setSelectedAddressId(addr.id)}
                      className="mt-0.5"
                    />
                    <div className="text-sm">
                      {addr.label && <p className="font-medium">{addr.label}</p>}
                      <p>{addr.street}, {addr.city}{addr.state ? `, ${addr.state}` : ""}</p>
                      <p>{addr.country} {addr.postal_code}</p>
                    </div>
                  </label>
                ))}
              </div>
            ) : null}

            <button
              onClick={() => setShowAddAddress(!showAddAddress)}
              className="mt-4 text-sm text-blue-600 hover:underline"
            >
              + Add new address
            </button>

            {showAddAddress && (
              <form onSubmit={handleAddAddress} className="mt-4 grid grid-cols-2 gap-3">
                {[
                  { key: "label", placeholder: "Label (e.g. Home)", full: true },
                  { key: "street", placeholder: "Street address", full: true },
                  { key: "city", placeholder: "City" },
                  { key: "state", placeholder: "State (optional)" },
                  { key: "country", placeholder: "Country" },
                  { key: "postal_code", placeholder: "Postal code" },
                ].map(({ key, placeholder, full }) => (
                  <input
                    key={key}
                    placeholder={placeholder}
                    value={(newAddr as Record<string, string>)[key]}
                    onChange={(e) => setNewAddr({ ...newAddr, [key]: e.target.value })}
                    className={`border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${full ? "col-span-2" : ""}`}
                  />
                ))}
                <button
                  type="submit"
                  className="col-span-2 bg-gray-900 text-white py-2 rounded-lg text-sm hover:bg-gray-800"
                >
                  Save Address
                </button>
              </form>
            )}
          </div>

          {/* Coupon */}
          <div className="bg-white border rounded-xl p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Coupon Code</h2>
            <CouponInput
              subtotal={subtotal}
              applied={couponResult}
              onApply={setCouponResult}
              onRemove={() => setCouponResult(null)}
            />
          </div>
        </div>

        {/* Right: Order Summary */}
        <div>
          <div className="bg-white border rounded-xl p-6 sticky top-24">
            <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
            <div className="space-y-2 text-sm mb-4">
              {cart?.items.map((item) => (
                <div key={item.id} className="flex justify-between text-gray-600">
                  <span className="truncate mr-2">{item.variant.name} ×{item.quantity}</span>
                  <span>{formatPrice(parseFloat(item.variant.price) * item.quantity)}</span>
                </div>
              ))}
            </div>
            <div className="border-t pt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span>{formatPrice(subtotal)}</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-{formatPrice(discount)}</span>
                </div>
              )}
              <div className="flex justify-between font-semibold text-base">
                <span>Total</span>
                <span>{formatPrice(total)}</span>
              </div>
            </div>

            <button
              onClick={handleSubmit}
              disabled={!selectedAddressId || placeOrder.isPending || !cart?.items.length}
              className="w-full mt-6 flex items-center justify-center gap-2 bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {placeOrder.isPending ? "Placing order..." : (
                <><CheckCircle size={18} /> Place Order</>
              )}
            </button>

            {placeOrder.isError && (
              <p className="text-red-500 text-xs mt-2 text-center">
                {(placeOrder.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Order failed"}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
