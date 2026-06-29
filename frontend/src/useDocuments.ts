import { useCallback, useEffect, useRef, useState } from 'react'
import { listDocuments } from './api'
import type { DocumentResponse } from './types'

const POLL_INTERVAL_MS = 2000

interface UseDocuments {
  documents: DocumentResponse[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/** Owns the document list: initial load, manual refetch, and polling while any row is `processing`. */
export function useDocuments(): UseDocuments {
  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    try {
      const data = await listDocuments()
      setDocuments(data.items)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refetch()
  }, [refetch])

  // Poll while any document is still processing; stop once none are.
  const processing = documents.some((d) => d.status === 'processing')
  const refetchRef = useRef(refetch)
  refetchRef.current = refetch
  useEffect(() => {
    if (!processing) return
    const id = setInterval(() => void refetchRef.current(), POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [processing])

  return { documents, loading, error, refetch }
}
