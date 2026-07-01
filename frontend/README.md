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

See `../CHANGELOG.md` for v0.1.0.
