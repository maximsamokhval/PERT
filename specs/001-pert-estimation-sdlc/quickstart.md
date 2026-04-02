# Quickstart: PERT Estimation SDLC Tool

**Feature**: `001-pert-estimation-sdlc`
**Purpose**: Get started guide for developers
**Prerequisites**: Python 3.12, Node.js 20+, pnpm, just

---

## 1. Clone & Install

```bash
# Clone repository
git clone <repository-url>
cd PERT_2_0

# Install all dependencies
just install
```

---

## 2. Environment Setup

### Backend

Create `backend/.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./pert.db

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-fernet-key-here

# JWT Settings
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS (for development)
CORS_ORIGINS=http://localhost:3000
```

### Frontend

Create `frontend/.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 3. Database Migration

```bash
# Apply all pending migrations
just be-migrate
```

---

## 4. Generate TypeScript Types

**Important**: Backend must be running first.

```bash
# Start backend in one terminal
just dev-be

# In another terminal, generate types
just fe-generate
```

---

## 5. Start Development Servers

### Option A: Two terminals (recommended)

```bash
# Terminal 1 - Backend
just dev-be

# Terminal 2 - Frontend
just dev-fe
```

### Option B: Manual start

```bash
# Backend
cd backend
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
pnpm dev
```

---

## 6. Access Application

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

---

## 7. Create First User

```bash
# Via API (example with curl)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "architect@example.com",
    "password": "SecurePassword123!",
    "display_name": "System Architect",
    "role": "editor"
  }'
```

---

## 8. Configure YouTrack (Optional)

1. Login as architect@example.com
2. Navigate to Settings
3. Enter YouTrack URL and API token
4. Click "Test Connection"
5. Select project and configure field mapping
6. Save

---

## Development Workflow

### Run Tests

```bash
# Backend tests with coverage
just be-test

# Frontend tests
just fe-test

# Frontend E2E (requires both servers running)
just fe-e2e
```

### Type Checking

```bash
# Both backend and frontend
just typecheck

# Backend only
just be-typecheck

# Frontend only
just fe-typecheck
```

### Linting

```bash
# Both backend and frontend
just lint

# Backend only
just be-lint

# Frontend only
just fe-lint
```

### Format Code

```bash
# Backend (ruff format)
just be-format

# Frontend (Prettier)
cd frontend && pnpm format
```

---

## Git Workflow

```bash
# Before committing
just ci

# Create new feature branch
git checkout -b feature/your-feature

# Commit changes (justfile handles hooks)
git commit -m "feat: your commit message"
```

**Note**: Pre-commit hooks run automatically on every commit.

---

## Project Structure

```
PERT_2_0/
├── backend/
│   ├── src/
│   │   ├── core/          # Config, DB, security
│   │   ├── features/      # Feature modules (sessions, items, export)
│   │   ├── shared/        # Shared models, protocols
│   │   └── main.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   ├── features/      # Feature modules
│   │   ├── components/    # Shared components
│   │   └── types/         # Generated types
│   └── package.json
├── specs/                 # Feature specifications
├── justfile               # Command runner
└── README.md
```

---

## Key Commands Reference

| Command | Description |
|---------|-------------|
| `just install` | Install all dependencies |
| `just dev-be` | Start backend dev server |
| `just dev-fe` | Start frontend dev server |
| `just be-migrate` | Apply DB migrations |
| `just fe-generate` | Generate TypeScript types |
| `just be-test` | Run backend tests |
| `just fe-test` | Run frontend tests |
| `just fe-e2e` | Run E2E tests |
| `just typecheck` | Type-check both |
| `just lint` | Lint both |
| `just ci` | Full CI check |

---

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Must be 3.12+

# Reinstall dependencies
cd backend && uv sync --all-extras
```

### Frontend TypeScript errors

```bash
# Regenerate types (backend must be running)
just fe-generate
```

### Database errors

```bash
# Reset database (WARNING: deletes all data)
rm backend/pert.db
just be-migrate
```

### Port already in use

```bash
# Backend on different port
uv run uvicorn src.main:app --reload --port 8001

# Frontend on different port
pnpm dev --port 3001
```

---

## Next Steps

1. Read [data-model.md](./data-model.md) for database schema
2. Review [contracts/](./contracts/) for API specifications
3. Check [constitution.md](../../.specify/memory/constitution.md) for architecture principles
4. Start implementing with `/speckit.tasks` command
