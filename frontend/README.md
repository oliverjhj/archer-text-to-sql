# Frontend

**Status:** Phase 4B scaffold - custom UI shell (internal reference, private WIP).

This is the custom Archer Text-to-SQL frontend: a Vite + React + TypeScript
application styled with the IBM Carbon Design System (dark `g100` theme). It
replaces the legacy Jinja templates and the embedded Watson Assistant widget
(still served by the backend and untouched during this phase).

Phase 4B delivers the static application shell only:

- Carbon UI Shell (header, side navigation, main workspace).
- A natural-language question input and an answer/result workspace.
- Loading, error, empty and answer states.

The workspace runs on **mock state only** - there is no live backend call yet.
Live integration with the backend `POST /ask` (via a future authenticated
`/api/ask` proxy) is deferred to Phase 4C.

## Prerequisites

- Node.js 20 LTS (or newer) and npm.

Node is not required to read the code, but is required to install dependencies,
type-check, build, or run the dev server.

## Install

```bash
cd frontend
npm install
```

This creates `node_modules/` and a `package-lock.json` (both git-ignored / to be
committed per project convention). No lockfile is committed yet because the
scaffold was authored on a machine without Node; run `npm install` to generate
it.

## Local development

Run the backend and the frontend dev server side by side.

Backend (from the repository root, in a separate terminal):

```bash
python -m uvicorn backend.main:app --reload --port 8080
```

Frontend (from `frontend/`):

```bash
npm run dev
```

The dev server runs on <http://localhost:5173>. `vite.config.ts` proxies the API
and legacy paths (`/api`, `/ask`, `/login`, `/landing`, `/chat`, `/static`,
`/favicon.ico`) to the backend on `http://localhost:8080`, so the frontend is
developed same-origin. This proxy is configured ahead of Phase 4C; the shell
does not call these paths yet.

Note: the backend downloads its database from IBM Cloud Object Storage at
startup and will not boot without valid COS configuration. The Phase 4B shell
does not depend on the backend running - you can develop the UI with `npm run
dev` alone.

## Type-check and build

```bash
npm run typecheck   # tsc -b (no emit)
npm run build       # tsc -b && vite build -> dist/
npm run preview     # serve the production build locally
```

## Environment

Copy `.env.example` to `.env.local` to override settings locally. The only
variable is `VITE_API_BASE_URL`, which should stay empty to use same-origin
relative paths (the dev proxy handles routing in development). **Do not put
secrets in any frontend environment file** - the backend API key is injected
server-side by the future `/api/ask` proxy, never in the browser.

## Project structure

```text
frontend/
  index.html            Vite entry document
  vite.config.ts        Vite config + dev proxy to the backend
  tsconfig*.json        TypeScript project references (app + node)
  .env.example          Documented env vars (no secrets)
  src/
    main.tsx            React root + Carbon styles import
    App.tsx             UI Shell composition (Theme g100)
    components/         AppHeader, AppSideNav, AskInput, AnswerWorkspace,
                        AnswerItem
    api/                client.ts (transport skeleton), ask.ts (/api/ask skeleton)
    hooks/              useAsk.ts (mock state machine)
    types/              api.ts (AskRequest/AskResponse/ConversationEntry)
    styles/             index.scss (Carbon import + layout)
```

## Deferred to later phases

- Phase 4C: the authenticated `/api/ask` backend proxy, live `/ask` integration,
  Markdown/table rendering of answers, and the legacy `/chat` replacement path.
- Phase 4D: accessibility/responsive polish, frontend tests, CI integration,
  deployment packaging, and legacy template/static removal.
