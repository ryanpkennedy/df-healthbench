# Development Environment Setup

## Quick Start

### Production Mode (Default)
```bash
make build
make up
make logs-backend
```

### Development Mode (Hot Reload)
```bash
make dev-up
make logs-backend
```

## How It Works

### Production Mode
- Uses final stage of Dockerfile (`production`)
- Copies source code into image
- Runs with 4 workers
- Requires rebuild for code changes
- Command: `docker-compose up`

### Development Mode
- Uses intermediate stage of Dockerfile (`development`)  
- Mounts source code as volume
- Runs with `--reload` flag (single worker)
- Code changes reload automatically
- Command: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

## Making Code Changes

### In Development Mode:
1. Edit files in `backend/app/`
2. Save the file
3. Watch logs: `make logs-backend`
4. Backend automatically reloads (takes ~2-3 seconds)
5. Test your changes immediately

### In Production Mode:
1. Edit files in `backend/app/`
2. Rebuild: `make build`
3. Restart: `make restart`
4. Changes are live

## Architecture

```
Dockerfile Structure:
├── Stage 1: builder (install dependencies)
├── Stage 2: development (hot-reload, mounted code)
└── Stage 3: production (4 workers, copied code) ← default
```

Production `docker-compose.yml`:
- No target specified → uses final stage (production)
- Copies code into image during build

Development `docker-compose.dev.yml` (override):
- Explicitly targets `development` stage
- Mounts `./backend/app` → `/app/app` (read-only)
- Changes reflected immediately

## Benefits

✅ **Production is unchanged** - Final stage remains the default
✅ **No rebuild needed** - Code changes reload automatically in dev
✅ **Same dependencies** - Both stages use same builder stage
✅ **Fast iteration** - Save file → reload in 2-3 seconds
✅ **Safe separation** - Dev and prod completely isolated

