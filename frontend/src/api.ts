import type { DocumentDetailResponse, DocumentListResponse } from './types'

/** Error carrying the HTTP status and the backend's `detail` message, when present. */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let detail = res.statusText
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') detail = body.detail
  } catch {
    // non-JSON body; keep statusText
  }
  return new ApiError(res.status, detail)
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const res = await fetch('/api/documents')
  if (!res.ok) throw await parseError(res)
  return res.json()
}

export async function uploadDocument(file: File, tags: string[]): Promise<DocumentDetailResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('tags', tags.join(','))
  const res = await fetch('/api/documents/upload', { method: 'POST', body: form })
  if (!res.ok) throw await parseError(res)
  return res.json()
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`/api/documents/${id}`, { method: 'DELETE' })
  if (!res.ok) throw await parseError(res)
}
