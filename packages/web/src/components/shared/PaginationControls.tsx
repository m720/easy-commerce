import { ChevronLeft, ChevronRight } from "lucide-react"

interface Props {
  page: number
  onPrev: () => void
  onNext: () => void
  hasPrev: boolean
  hasNext: boolean
}

export default function PaginationControls({ page, onPrev, onNext, hasPrev, hasNext }: Props) {
  return (
    <div className="flex items-center justify-center gap-4 py-6">
      <button
        onClick={onPrev}
        disabled={!hasPrev}
        className="flex items-center gap-1 px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
      >
        <ChevronLeft size={16} /> Prev
      </button>
      <span className="text-sm text-gray-600">Page {page}</span>
      <button
        onClick={onNext}
        disabled={!hasNext}
        className="flex items-center gap-1 px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
      >
        Next <ChevronRight size={16} />
      </button>
    </div>
  )
}
