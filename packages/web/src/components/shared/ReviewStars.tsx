import { Star } from "lucide-react"

interface Props {
  rating: number
  max?: number
  size?: number
}

export default function ReviewStars({ rating, max = 5, size = 16 }: Props) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: max }).map((_, i) => (
        <Star
          key={i}
          size={size}
          className={i < rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}
        />
      ))}
    </div>
  )
}
