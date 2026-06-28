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
- [ ] Document management UI
  - upload form (file picker + tag input, multiple tags)
  - document list table (filename, tags, upload date, chunk count)
  - delete action per row
  - API client hitting `/api/...` (proxied in dev via vite, via nginx in prod)
