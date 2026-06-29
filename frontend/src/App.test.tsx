import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { DocumentResponse } from './types'

function makeDoc(overrides: Partial<DocumentResponse> = {}): DocumentResponse {
  return {
    id: 'id-1',
    filename: 'report.pdf',
    content_type: 'application/pdf',
    size_bytes: 2048,
    content_hash: 'abc',
    tags: ['compliance'],
    status: 'ready',
    error_message: null,
    chunk_count: 3,
    created_at: '2026-06-29T10:00:00Z',
    updated_at: '2026-06-29T10:00:00Z',
    ...overrides,
  }
}

function listResponse(body: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({ ok, status, json: async () => body } as Response)
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', listResponse({ items: [], total: 0 }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('renders the app shell heading', async () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /document intelligence server/i })).toBeDefined()
    await waitFor(() => screen.getByText(/no documents yet/i))
  })

  it('shows the empty state when there are no documents', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText(/no documents yet/i)).toBeDefined())
  })

  it('renders document rows', async () => {
    vi.stubGlobal('fetch', listResponse({ items: [makeDoc()], total: 1 }))
    render(<App />)
    await waitFor(() => expect(screen.getByText('report.pdf')).toBeDefined())
    expect(screen.getByText('compliance')).toBeDefined()
    expect(screen.getByText('ready')).toBeDefined()
  })

  it('shows an error state with retry when the list request fails', async () => {
    vi.stubGlobal('fetch', listResponse({ detail: 'boom' }, false, 500))
    render(<App />)
    await waitFor(() => expect(screen.getByText('boom')).toBeDefined())
    expect(screen.getByRole('button', { name: /retry/i })).toBeDefined()
  })

  it('uploads a file then closes the modal and refetches', async () => {
    let uploaded = false
    const fetchMock = vi.fn(async (url: string) => {
      if (url === '/api/documents/upload') {
        uploaded = true
        return {
          ok: true,
          status: 202,
          json: async () => makeDoc({ status: 'processing' }),
        } as Response
      }
      const items = uploaded ? [makeDoc()] : []
      return {
        ok: true,
        status: 200,
        json: async () => ({ items, total: items.length }),
      } as Response
    })
    vi.stubGlobal('fetch', fetchMock as unknown as typeof fetch)

    render(<App />)
    await waitFor(() => screen.getByText(/no documents yet/i))
    fireEvent.click(screen.getByRole('button', { name: /upload/i }))

    const file = new File(['hello'], 'report.pdf', { type: 'application/pdf' })
    const dialog = screen.getByRole('dialog')
    const input = screen.getByLabelText(/file/i) as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    fireEvent.change(input)
    fireEvent.submit(within(dialog).getByRole('button', { name: /^upload$/i }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/documents/upload',
        expect.objectContaining({ method: 'POST' }),
      ),
    )
    await waitFor(() => expect(screen.getByText('report.pdf')).toBeDefined())
  })

  it('deletes a document after confirmation and refetches', async () => {
    let deleted = false
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        deleted = true
        return { ok: true, status: 204, json: async () => undefined } as Response
      }
      const items = deleted ? [] : [makeDoc()]
      return {
        ok: true,
        status: 200,
        json: async () => ({ items, total: items.length }),
      } as Response
    })
    vi.stubGlobal('fetch', fetchMock as unknown as typeof fetch)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<App />)
    await waitFor(() => screen.getByText('report.pdf'))
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))

    await waitFor(() => expect(screen.getByText(/no documents yet/i)).toBeDefined())
    expect(fetchMock).toHaveBeenCalledWith('/api/documents/id-1', { method: 'DELETE' })
  })
})
