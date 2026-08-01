import { useState } from "react"
import { useAdminReturns, useApproveReturn, useRejectReturn } from "@/api/returns"
import { formatDate } from "@/lib/utils"
import { usePagination } from "@/hooks/usePagination"
import PaginationControls from "@/components/shared/PaginationControls"
import type { ReturnStatus, UUID } from "@/types"

const statusConfig: Record<ReturnStatus, { label: string; className: string }> = {
  pending: { label: "Pending", className: "bg-yellow-100 text-yellow-800" },
  approved: { label: "Approved", className: "bg-green-100 text-green-800" },
  rejected: { label: "Rejected", className: "bg-red-100 text-red-800" },
}

export default function ReturnsPage() {
  const { skip, limit, page, nextPage, prevPage } = usePagination(20)
  const { data: returns, isLoading } = useAdminReturns({ skip, limit })
  const approveReturn = useApproveReturn()
  const rejectReturn = useRejectReturn()

  // Track which row is showing notes input and what action
  const [actionRow, setActionRow] = useState<{ id: UUID; type: "approve" | "reject" } | null>(null)
  const [notes, setNotes] = useState("")

  const handleAction = async () => {
    if (!actionRow) return
    if (actionRow.type === "approve") {
      await approveReturn.mutateAsync({ returnId: actionRow.id, admin_notes: notes || undefined })
    } else {
      await rejectReturn.mutateAsync({ returnId: actionRow.id, admin_notes: notes || undefined })
    }
    setActionRow(null)
    setNotes("")
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-charcoal">Return Requests</h1>

      <div className="bg-white border border-sage/30 rounded-nested shadow-soft overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 bg-sage/20 animate-pulse rounded" />
            ))}
          </div>
        ) : !returns || returns.length === 0 ? (
          <div className="text-center py-12 text-charcoal/70">
            <p className="font-medium">No return requests</p>
            <p className="text-sm mt-1">All clear! No pending returns.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-cream border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-charcoal/70">Return ID</th>
                  <th className="px-4 py-3 text-left font-medium text-charcoal/70">Order ID</th>
                  <th className="px-4 py-3 text-left font-medium text-charcoal/70">Reason</th>
                  <th className="px-4 py-3 text-center font-medium text-charcoal/70">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-charcoal/70">Date</th>
                  <th className="px-4 py-3 text-left font-medium text-charcoal/70">Actions</th>
                </tr>
              </thead>
              <tbody>
                {returns.map((ret) => (
                  <>
                    <tr key={ret.id} className="border-b last:border-0 hover:bg-cream">
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-charcoal/70 bg-sage/20 px-2 py-0.5 rounded">
                          {ret.id.slice(0, 8)}…
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-charcoal/70">
                          {ret.order_id.slice(0, 8)}…
                        </span>
                      </td>
                      <td className="px-4 py-3 text-charcoal/80 max-w-xs truncate">{ret.reason}</td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig[ret.status].className}`}
                        >
                          {statusConfig[ret.status].label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-charcoal/70 whitespace-nowrap">
                        {formatDate(ret.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setActionRow({ id: ret.id, type: "approve" })
                              setNotes(ret.admin_notes ?? "")
                            }}
                            disabled={ret.status !== "pending" || approveReturn.isPending}
                            className="px-3 py-1 text-xs font-medium bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => {
                              setActionRow({ id: ret.id, type: "reject" })
                              setNotes(ret.admin_notes ?? "")
                            }}
                            disabled={ret.status !== "pending" || rejectReturn.isPending}
                            className="px-3 py-1 text-xs font-medium bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                    {actionRow?.id === ret.id && (
                      <tr key={`action-${ret.id}`} className="bg-cream border-b">
                        <td colSpan={6} className="px-4 py-3">
                          <div className="flex flex-col gap-2 max-w-lg">
                            <p className="text-sm font-medium text-charcoal/80">
                              {actionRow.type === "approve" ? "Approving" : "Rejecting"} return —{" "}
                              <span className="text-charcoal/70">add admin notes (optional)</span>
                            </p>
                            <textarea
                              value={notes}
                              onChange={(e) => setNotes(e.target.value)}
                              rows={2}
                              placeholder="Admin notes..."
                              className="border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/40 resize-none"
                            />
                            <div className="flex gap-2">
                              <button
                                onClick={handleAction}
                                disabled={approveReturn.isPending || rejectReturn.isPending}
                                className={`px-4 py-1.5 text-sm font-medium text-white rounded disabled:opacity-50 ${
                                  actionRow.type === "approve"
                                    ? "bg-green-600 hover:bg-green-700"
                                    : "bg-red-600 hover:bg-red-700"
                                }`}
                              >
                                {approveReturn.isPending || rejectReturn.isPending
                                  ? "Processing..."
                                  : `Confirm ${actionRow.type === "approve" ? "Approval" : "Rejection"}`}
                              </button>
                              <button
                                onClick={() => { setActionRow(null); setNotes("") }}
                                className="px-4 py-1.5 text-sm border rounded hover:bg-sage/20"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
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

      <PaginationControls
        page={page}
        hasPrev={skip > 0}
        hasNext={!!returns && returns.length === limit}
        onPrev={prevPage}
        onNext={nextPage}
      />
    </div>
  )
}
