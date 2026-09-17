# BAMP frontend

Next.js (App Router) + TypeScript + Tailwind + Recharts. Runs at http://localhost:3000.

**Not implemented yet** — every route under `src/app/` is a placeholder naming the SRS section it will
implement, so the app's shape is visible before the UI is built (see `CLAUDE.md`).

| Route | Screen (SRS §3.1.2) |
|---|---|
| `/drones`, `/drones/new` | Drone List / Custom Drone Form |
| `/missions` | Mission Builder + Flight Leg Editor + Wind Speed + Model selection |
| `/simulation` | Simulation & Feasibility Results |
| `/comparison` | Drone Comparison View |
| `/scenarios` | Scenario Manager |
| `/models` | Model & Version registry (read-only, no export) |
| `/training` | Custom Model Training (FE-09) |

The backend base URL is `NEXT_PUBLIC_API_URL` (see `src/lib/api.ts`).
