import { useState } from "react"

export function usePagination(defaultLimit = 20) {
  const [skip, setSkip] = useState(0)
  const [limit] = useState(defaultLimit)

  const page = Math.floor(skip / limit) + 1

  const nextPage = () => setSkip((s) => s + limit)
  const prevPage = () => setSkip((s) => Math.max(0, s - limit))
  const goToPage = (p: number) => setSkip((p - 1) * limit)
  const reset = () => setSkip(0)

  return { skip, limit, page, nextPage, prevPage, goToPage, reset }
}
