import { type KeyboardEvent, useState } from 'react'

interface Props {
  tags: string[]
  onChange: (tags: string[]) => void
}

/** Type a tag and press Enter (or comma) to add a removable chip. */
export function TagInput({ tags, onChange }: Props) {
  const [draft, setDraft] = useState('')

  const add = () => {
    const value = draft.trim()
    if (value && !tags.includes(value)) onChange([...tags, value])
    setDraft('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      add()
    } else if (e.key === 'Backspace' && !draft && tags.length > 0) {
      onChange(tags.slice(0, -1))
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-1 rounded border border-gray-700 bg-gray-900 px-2 py-1">
      {tags.map((tag) => (
        <span
          key={tag}
          className="flex items-center gap-1 rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-200"
        >
          {tag}
          <button
            type="button"
            aria-label={`Remove ${tag}`}
            onClick={() => onChange(tags.filter((t) => t !== tag))}
            className="text-gray-400 hover:text-gray-100"
          >
            ×
          </button>
        </span>
      ))}
      <input
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={add}
        placeholder="Add tag…"
        className="flex-1 bg-transparent px-1 py-0.5 text-sm text-gray-100 outline-none"
      />
    </div>
  )
}
