import type { OrderStatus } from "@/types"
import { cn } from "@/lib/utils"

const statusConfig: Record<OrderStatus, { label: string; className: string }> = {
  pending:    { label: "Pending",    className: "bg-yellow-100 text-yellow-800" },
  processing: { label: "Processing", className: "bg-indigo-100 text-indigo-800" },
  shipped:    { label: "Shipped",    className: "bg-indigo-100 text-indigo-800" },
  delivered:  { label: "Delivered",  className: "bg-green-100 text-green-800" },
  cancelled:  { label: "Cancelled",  className: "bg-red-100 text-red-800" },
  returned:   { label: "Returned",   className: "bg-zinc-100 text-zinc-800" },
}

export default function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const config = statusConfig[status]
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", config.className)}>
      {config.label}
    </span>
  )
}
