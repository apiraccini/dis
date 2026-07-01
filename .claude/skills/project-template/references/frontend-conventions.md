# Frontend Conventions

## Stack

- Framework: React + Vite + TypeScript
- Package manager: Bun
- Linting and formatting: Biome (replaces ESLint + Prettier)
- Testing: Vitest + @testing-library/react; Playwright only if E2E is needed

## Project setup

```bash
cd frontend
bun create vite . --template react-ts
bun add <deps>
bun run dev
```

## Linting (Biome 2.x)

Biome 2 config — note `organizeImports` moved under `assist` (the 1.x top-level key is rejected by Biome 2). Match the `$schema` version to the installed `@biomejs/biome`.

```json
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "assist": {
    "actions": { "source": { "organizeImports": "on" } }
  },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "asNeeded",
      "trailingCommas": "all"
    }
  }
}
```

## package.json scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "biome check src/",
    "lint:fix": "biome check --write src/",
    "format": "biome format --write src/",
    "test": "vitest run"
  }
}
```

- `tsc -b` (not bare `tsc`): the Vite react-ts template uses tsconfig project references, where bare `tsc` errors.
- The write/fix flag in Biome 2 is `--write` (`--apply` was removed).

## Vitest config

Do NOT put `test: { ... }` inside `vite.config.ts`; the key is not in the Vite plugin's types and causes type errors. Use a separate `vitest.config.ts`:

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
    passWithNoTests: true,
  },
})
```

`passWithNoTests: true` matters during scaffolding: without it `vitest run` exits 1 when no test files exist, breaking CI.

The scaffold ships one render smoke test so vitest exercises something real from day one:

```tsx
// src/App.test.tsx
import { render, screen } from '@testing-library/react'
import App from './App'

test('renders the app shell', () => {
  render(<App />)
  expect(screen.getByRole('heading')).toBeDefined()
})
```

The smoke test is deliberately router-free; if the project adds react-router later, wrap the render in `MemoryRouter` then.

## Dockerfile

Static build served by nginx. Prefer the official `oven/bun` image over installing bun into a node image.

```dockerfile
FROM oven/bun:1 AS builder
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Minimal `frontend/nginx.conf` — serves the SPA and proxies `/api/` to the backend compose service:

```nginx
# frontend/nginx.conf
server {
    listen 80;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The `proxy_pass` host (`backend`) must match the backend service name in `docker-compose.yml`. The trailing slash on `http://backend:8000/` strips the `/api` prefix; drop it if the backend routes are mounted under `/api` themselves.
