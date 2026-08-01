import { useState } from "react"
import { useForm } from "react-hook-form"
import { Plus, Pencil, Trash2, X, Check } from "lucide-react"
import { useCoupons, useCreateCoupon, useUpdateCoupon, useDeleteCoupon } from "@/api/coupons"
import { formatPrice, formatDate } from "@/lib/utils"
import type { Coupon, CouponType } from "@/types"

interface CouponFormValues {
  code: string
  type: CouponType
  value: string
  min_order_amount: string
  max_uses: string
  expires_at: string
  is_active: boolean
}

const emptyForm: CouponFormValues = {
  code: "",
  type: "percent",
  value: "",
  min_order_amount: "",
  max_uses: "",
  expires_at: "",
  is_active: true,
}

export default function CouponsPage() {
  const { data: coupons, isLoading } = useCoupons()
  const createCoupon = useCreateCoupon()
  const updateCoupon = useUpdateCoupon()
  const deleteCoupon = useDeleteCoupon()

  const [showAddForm, setShowAddForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  const addForm = useForm<CouponFormValues>({ defaultValues: emptyForm })
  const editForm = useForm<CouponFormValues>()

  const buildPayload = (data: CouponFormValues) => ({
    code: data.code.toUpperCase(),
    type: data.type,
    value: data.value,
    min_order_amount: data.min_order_amount || undefined,
    max_uses: data.max_uses ? Number(data.max_uses) : undefined,
    expires_at: data.expires_at || undefined,
    is_active: data.is_active,
  })

  const handleCreate = async (data: CouponFormValues) => {
    await createCoupon.mutateAsync(buildPayload(data))
    addForm.reset(emptyForm)
    setShowAddForm(false)
  }

  const handleEdit = (coupon: Coupon) => {
    setEditingId(coupon.id)
    editForm.reset({
      code: coupon.code,
      type: coupon.type,
      value: coupon.value,
      min_order_amount: coupon.min_order_amount ?? "",
      max_uses: coupon.max_uses ? String(coupon.max_uses) : "",
      expires_at: coupon.expires_at ? coupon.expires_at.slice(0, 10) : "",
      is_active: coupon.is_active,
    })
  }

  const handleUpdate = async (data: CouponFormValues) => {
    if (!editingId) return
    await updateCoupon.mutateAsync({ id: editingId, ...buildPayload(data) })
    setEditingId(null)
  }

  const handleDelete = (id: string, code: string) => {
    if (window.confirm(`Delete coupon "${code}"?`)) {
      deleteCoupon.mutate(id)
    }
  }

  const CouponFormFields = ({ form }: { form: ReturnType<typeof useForm<CouponFormValues>> }) => (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Code *</label>
        <input
          {...form.register("code", { required: true })}
          className="w-full border rounded px-2 py-1.5 text-sm uppercase focus:outline-none focus:ring-2 focus:ring-indigo-300"
          placeholder="SAVE20"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Type *</label>
        <select
          {...form.register("type")}
          className="w-full border rounded px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
        >
          <option value="percent">Percent (%)</option>
          <option value="fixed">Fixed ($)</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Value *</label>
        <input
          {...form.register("value", { required: true })}
          type="number"
          step="0.01"
          min="0"
          className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          placeholder="20"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Min Order Amount</label>
        <input
          {...form.register("min_order_amount")}
          type="number"
          step="0.01"
          min="0"
          className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          placeholder="0.00"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Max Uses</label>
        <input
          {...form.register("max_uses")}
          type="number"
          min="1"
          className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          placeholder="Unlimited"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-zinc-600 mb-1">Expires At</label>
        <input
          {...form.register("expires_at")}
          type="date"
          className="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
      </div>
      <div className="col-span-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" {...form.register("is_active")} className="rounded border-zinc-300" />
          <span className="text-sm text-zinc-700">Active</span>
        </label>
      </div>
    </div>
  )

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-900">Coupons</h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} /> Add Coupon
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 p-5 space-y-4">
          <h2 className="text-base font-semibold text-zinc-800">New Coupon</h2>
          <form onSubmit={addForm.handleSubmit(handleCreate)} className="space-y-4">
            <CouponFormFields form={addForm} />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={addForm.formState.isSubmitting}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => { setShowAddForm(false); addForm.reset(emptyForm) }}
                className="border px-4 py-2 rounded-lg text-sm hover:bg-zinc-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white border border-zinc-200 rounded-xl shadow-sm shadow-zinc-900/5 overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-zinc-100 animate-pulse rounded" />
            ))}
          </div>
        ) : !coupons || coupons.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">
            <p className="font-medium">No coupons yet</p>
            <p className="text-sm mt-1">Create your first coupon above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Code</th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Type</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Value</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Min Order</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Max Uses</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Used</th>
                  <th className="px-4 py-3 text-left font-medium text-zinc-600">Expires</th>
                  <th className="px-4 py-3 text-center font-medium text-zinc-600">Active</th>
                  <th className="px-4 py-3 text-right font-medium text-zinc-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {coupons.map((coupon) => (
                  <>
                    <tr key={coupon.id} className="border-b last:border-0 hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <span className="font-mono font-semibold text-zinc-900 bg-zinc-100 px-2 py-0.5 rounded text-xs">
                          {coupon.code}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-600 capitalize">{coupon.type}</td>
                      <td className="px-4 py-3 text-right font-medium text-zinc-900">
                        {coupon.type === "percent"
                          ? `${parseFloat(coupon.value)}%`
                          : formatPrice(coupon.value)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-600">
                        {coupon.min_order_amount ? formatPrice(coupon.min_order_amount) : "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-600">
                        {coupon.max_uses ?? "∞"}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-600">{coupon.used_count}</td>
                      <td className="px-4 py-3 text-zinc-600 whitespace-nowrap">
                        {coupon.expires_at ? formatDate(coupon.expires_at) : "Never"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            coupon.is_active ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
                          }`}
                        >
                          {coupon.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleEdit(coupon)}
                            className="p-1.5 text-zinc-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(coupon.id, coupon.code)}
                            disabled={deleteCoupon.isPending}
                            className="p-1.5 text-zinc-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                    {editingId === coupon.id && (
                      <tr key={`edit-${coupon.id}`} className="bg-indigo-50 border-b">
                        <td colSpan={9} className="px-4 py-4">
                          <form onSubmit={editForm.handleSubmit(handleUpdate)} className="space-y-4">
                            <h3 className="text-sm font-medium text-zinc-700">Edit Coupon</h3>
                            <CouponFormFields form={editForm} />
                            <div className="flex gap-2">
                              <button
                                type="submit"
                                disabled={editForm.formState.isSubmitting}
                                className="p-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                              >
                                <Check size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingId(null)}
                                className="p-1.5 border rounded hover:bg-zinc-100"
                              >
                                <X size={14} />
                              </button>
                            </div>
                          </form>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
