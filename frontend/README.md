# Frontend

React SPA for document management (upload + tag, list, delete).

## Stack
- React 19 + Vite + TypeScript (scaffolded with `bun create vite . --template react-ts`)
- Bun, Biome 2.x, Vitest

## Tree
```
src/
├── main.tsx            entrypoint
├── App.tsx             app shell: wires useDocuments + upload/delete actions
├── App.test.tsx        render smoke test
├── DocumentTable.tsx   document list: tags, status, size, chunk count
├── UploadModal.tsx     upload form (file + tags), busy/error states
├── TagInput.tsx        tag chip input, used by the upload form
├── StatusBadge.tsx     processing/ready/failed badge with error tooltip
├── useDocuments.ts     data hook: fetch + poll while any doc is processing
├── api.ts              REST client (upload/list/delete), ApiError type
├── types.ts            shared frontend types (Document, Tag, etc.)
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

See `../CHANGELOG.md` for v0.1.0.
