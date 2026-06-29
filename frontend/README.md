# Frontend

React SPA for document management (upload + tag, list, delete).

## Stack
- React 19 + Vite + TypeScript (scaffolded with `bun create vite . --template react-ts`)
- Bun, Biome 2.x, Vitest

## Tree
```
src/
├── main.tsx            entrypoint
├── App.tsx             app shell (scaffold)
├── App.test.tsx        render smoke test
├── test-setup.ts       @testing-library/jest-dom
└── index.css
nginx.conf              SPA serving + /api proxy to backend
Dockerfile              bun build → nginx
```

## Development
```bash
bun install
bun run dev              # dev server at :5173, proxies /api to :8000
bun run build            # tsc -b && vite build
bun run lint             # biome check src/
bun run test             # vitest
```

## Backlog

### v0.1.0
- [x] Document management UI — minimal but functional (REQUEST.md §A; eval priority 5, not graded on design)
  - Foundation: Tailwind setup; TS types mirroring `DocumentResponse`/`DocumentListResponse`/`DocumentStatus`; typed `fetch` client over `/api/*` (`listDocuments`, `uploadDocument`, `deleteDocument`); app shell
  - Upload form: file picker (PDF + text min) + multi-tag input → `POST /api/documents/upload`; handle 200 (dedup), 202 (processing), 422 (parse error)
  - Document list table: filename, tags, status badge, size, chunk count, upload date; loading/empty/error states; poll while any row is `processing`
  - Delete action per row (confirm → `DELETE`, refetch)
  - Tests (Vitest) + Biome clean + `bun run build` green; verify end-to-end against the live Docker stack
