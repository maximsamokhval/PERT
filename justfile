# PERT Estimation App — task runner
# Usage: just <recipe>   (requires https://github.com/casey/just)

set shell := ["cmd.exe", "/c"]

# ── backend ────────────────────────────────────────────────────────────────────

# Install backend dependencies
be-sync:
    cd backend && uv sync --all-extras

# Apply all pending DB migrations
be-migrate:
    cd backend && uv run alembic upgrade head

# Start backend dev server (port 8000)
be-dev:
    cd backend && uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# Run full backend test suite with coverage
be-test:
    cd backend && uv run pytest --cov=src

# Run a single test file
be-test-file file:
    cd backend && uv run pytest {{file}} -v

# mypy strict type-check
be-typecheck:
    cd backend && uv run mypy src/

# Type-check + lint single file (agent calls after every file)
be-check-file file:
    cd backend && uv run mypy {{file}} && uv run ruff check {{file}}

# ruff lint
be-lint:
    cd backend && uv run ruff check src/

# ruff auto-format
be-format:
    cd backend && uv run ruff format src/

# Generate new Alembic migration  →  just be-revision "describe change"
be-revision msg:
    cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

# Show Alembic migration history
be-history:
    cd backend && uv run alembic history

# ── frontend ───────────────────────────────────────────────────────────────────

# Install frontend dependencies
fe-install:
    cd frontend && pnpm install

# Start Next.js dev server (port 3000)
fe-dev:
    cd frontend && pnpm dev

# Generate TypeScript types from live backend OpenAPI spec
# Backend must be running on :8000 before calling this recipe
fe-generate:
    cd frontend && pnpm openapi-typescript http://127.0.0.1:8000/openapi.json -o src/types/api.ts

# Run full test suite
fe-test:
    cd frontend && pnpm test

# Run Playwright E2E tests (requires both servers running)
fe-e2e:
    cd frontend && pnpm test:e2e

# TypeScript type-check (tsc --noEmit)
fe-typecheck:
    cd frontend && pnpm typecheck

# ESLint
fe-lint:
    cd frontend && pnpm eslint src/

# Production build
fe-build:
    cd frontend && pnpm build

# ── combined ───────────────────────────────────────────────────────────────────

# Install all dependencies (backend + frontend)
install: be-sync fe-install

# Type-check both backend and frontend
typecheck: be-typecheck fe-typecheck

# Lint both backend and frontend
lint: be-lint fe-lint

# Start both dev servers (Windows: separate terminals required)
dev-be:
    just be-dev

dev-fe:
    just fe-dev

# Run full CI check suite locally before push
ci: be-typecheck be-lint be-test fe-typecheck fe-lint fe-test