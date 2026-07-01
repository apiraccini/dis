import { useState } from 'react'
import { deleteDocument } from './api'
import { DocumentTable } from './DocumentTable'
import type { DocumentResponse } from './types'
import { UploadModal } from './UploadModal'
import { useDocuments } from './useDocuments'

function App() {
  const { documents, loading, error, refetch } = useDocuments()
  const [showUpload, setShowUpload] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const handleDelete = async (doc: DocumentResponse) => {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return
    setDeleteError(null)
    try {
      await deleteDocument(doc.id)
      await refetch()
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete document.')
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-100">Document Intelligence Server</h1>
          <p className="text-sm text-gray-400">Upload, tag, and manage documents.</p>
        </div>
        <button
          type="button"
          onClick={() => setShowUpload(true)}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Upload
        </button>
      </header>

      {deleteError && (
        <p className="mb-4 rounded border border-red-800 bg-red-950 px-4 py-2 text-sm text-red-300">
          {deleteError}
        </p>
      )}

      <div className="rounded-lg border border-gray-800">
        <DocumentTable
          documents={documents}
          loading={loading}
          error={error}
          onRetry={refetch}
          onDelete={handleDelete}
        />
      </div>

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onUploaded={refetch} />}
    </div>
  )
}

export default App
