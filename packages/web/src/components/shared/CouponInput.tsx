import { useState } from "react"
import { useValidateCoupon } from "@/api/coupons"
import type { CouponValidateResponse } from "@/types"
import { formatPrice } from "@/lib/utils"

interface Props {
  subtotal: string
  onApply: (result: CouponValidateResponse) => void
  onRemove: () => void
  applied: CouponValidateResponse | null
}

export default function CouponInput({ subtotal, onApply, onRemove, applied }: Props) {
  const [code, setCode] = useState("")
  const [error, setError] = useState("")
  const validate = useValidateCoupon()

  const handleApply = () => {
    setError("")
    validate.mutate(
      { code: code.trim(), order_subtotal: subtotal },
      {
        onSuccess: (res) => {
          if (res.valid) {
            onApply(res)
          } else {
            setError("Coupon is not valid.")
          }
        },
        onError: (err: unknown) => {
          const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Invalid coupon"
          setError(msg)
        },
      }
    )
  }

  if (applied) {
    return (
      <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
        <div>
          <p className="text-sm font-medium text-green-800">Coupon applied: <strong>{applied.coupon.code}</strong></p>
          <p className="text-sm text-green-600">-{formatPrice(applied.discount_amount)} discount</p>
        </div>
        <button onClick={onRemove} className="text-sm text-red-600 hover:underline">Remove</button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter coupon code"
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
          onKeyDown={(e) => e.key === "Enter" && handleApply()}
        />
        <button
          onClick={handleApply}
          disabled={validate.isPending || !code.trim()}
          className="px-4 py-2 bg-brand text-white text-sm rounded-lg hover:bg-brand/90 disabled:opacity-50"
        >
          {validate.isPending ? "..." : "Apply"}
        </button>
      </div>
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  )
}
