import { StatusBadge } from './StatusBadge'
import type { DocumentResponse } from './types'

interface Props {
  documents: DocumentResponse[]
  loading: boolean
  error: string | null
  onRetry: () => void
  onDelete: (doc: DocumentResponse) => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

export function DocumentTable({ documents, loading, error, onRetry, onDelete }: Props) {
  if (loading) return <p className="p-6 text-gray-400">Loading documents…</p>

  if (error) {
    return (
      <div className="p-6 text-red-300">
        <p>{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded bg-gray-700 px-3 py-1 text-sm text-gray-100 hover:bg-gray-600"
        >
          Retry
        </button>
      </div>
    )
  }

  if (documents.length === 0) {
    return <p className="p-6 text-gray-400">No documents yet. Upload one to get started.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-700 text-gray-400">
          <tr>
            <th className="px-4 py-2 font-medium">Filename</th>
            <th className="px-4 py-2 font-medium">Tags</th>
            <th className="px-4 py-2 font-medium">Status</th>
            <th className="px-4 py-2 font-medium">Size</th>
            <th className="px-4 py-2 font-medium">Chunks</th>
            <th className="px-4 py-2 font-medium">Uploaded</th>
            <th className="px-4 py-2 font-medium" />
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b border-gray-800">
              <td className="px-4 py-2 text-gray-100">{doc.filename}</td>
              <td className="px-4 py-2">
                <div className="flex flex-wrap gap-1">
                  {doc.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-200"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-2">
                <StatusBadge status={doc.status} errorMessage={doc.error_message} />
              </td>
              <td className="px-4 py-2 text-gray-300">{formatSize(doc.size_bytes)}</td>
              <td className="px-4 py-2 text-gray-300">{doc.chunk_count}</td>
              <td className="px-4 py-2 text-gray-300">{formatDate(doc.created_at)}</td>
              <td className="px-4 py-2 text-right">
                <button
                  type="button"
                  onClick={() => onDelete(doc)}
                  className="rounded px-2 py-1 text-xs text-red-300 hover:bg-red-500/10"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
