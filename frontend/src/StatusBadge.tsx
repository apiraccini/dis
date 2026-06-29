import type { DocumentStatus } from './types'

const STYLES: Record<DocumentStatus, string> = {
  processing: 'bg-amber-500/15 text-amber-300',
  ready: 'bg-emerald-500/15 text-emerald-300',
  failed: 'bg-red-500/15 text-red-300',
}

interface Props {
  status: DocumentStatus
  errorMessage?: string | null
}

export function StatusBadge({ status, errorMessage }: Props) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
      title={status === 'failed' && errorMessage ? errorMessage : undefined}
    >
      {status}
    </span>
  )
}
