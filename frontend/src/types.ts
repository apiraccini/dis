export type DocumentStatus = 'processing' | 'ready' | 'failed'

export interface DocumentResponse {
  id: string
  filename: string
  content_type: string | null
  size_bytes: number
  content_hash: string
  tags: string[]
  status: DocumentStatus
  error_message: string | null
  chunk_count: number
  created_at: string
  updated_at: string
}

export interface DocumentDetailResponse extends DocumentResponse {
  parsed_text: string
}

export interface DocumentListResponse {
  items: DocumentResponse[]
  total: number
}
