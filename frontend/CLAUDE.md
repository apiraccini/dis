# Frontend — Document Intelligence Server

## Stack
- React + Vite + TypeScript (scaffolded with `bun create vite . --template react-ts`)
- Bun (package manager), Biome (lint + format), Vitest (tests)

## Quick commands
- `cd frontend && bun install`: install deps
- `bun run dev`: dev server
- `bun run build`: production build
- `bun run lint`: biome check
- `bun run test`: vitest

## Rules
- Biome config in `biome.json` (2.x). The `$schema` version must match the installed `@biomejs/biome`.
- `vitest.config.ts` is separate from `vite.config.ts` (the Vite plugin types reject a `test` key in vite config).
- Dev server proxies `/api` to `http://localhost:8000` (see `vite.config.ts`).
