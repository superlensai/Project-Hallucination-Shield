# HalWall — Trusted Package Database

HalWall is a supply-chain security service that crawls package registries, computes trust scores, detects hallucinated package names, and exposes a fast lookup API for developer tools and CI pipelines.

## Features

- **Trust scoring** — Automated scoring (0–100) of packages from PyPI, npm, crates.io, and Go modules
- **Hallucination detection** — Track and flag package names that AI models frequently hallucinate but don't exist on registries
- **Signed snapshots** — TUF-inspired Merkle-tree snapshots for offline trust verification
- **Database gate** — Production-grade connection pooling, circuit breaker, query timeouts, and read-replica routing
- **API key auth** — Scoped keys with per-key rate limiting
- **Rate limiting** — Redis-backed sliding window, per-IP for anonymous access

## Quick Start (Development)

```bash
# Clone
git clone https://github.com/your-org/halwall.git
cd halwall

# Start services (dev mode with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Run migrations
docker compose exec api alembic upgrade head

# Create the first admin API key
docker compose exec api python -m scripts.create_admin_key
```

The API is now at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

## Production Deployment

```bash
# Copy and fill in secrets
cp .env.example .env
# Edit .env with real passwords, keys, etc.

# Deploy
docker compose up -d --build

# Run migrations
docker compose exec api alembic upgrade head

# Bootstrap admin key
docker compose exec api python -m scripts.create_admin_key
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/internal/health` | None | Liveness probe |
| GET | `/internal/health/db` | None | Deep health check with DB pool stats |
| POST | `/internal/trust/lookup` | Rate-limited | Look up trust score for a package |
| POST | `/internal/trust/bulk` | Rate-limited | Bulk trust lookup |
| POST | `/internal/hallucination/report` | `write` scope | Report a hallucinated package |
| GET | `/internal/snapshot/latest` | Rate-limited | Get latest trust snapshot |
| POST | `/internal/admin/keys` | `admin` scope | Create an API key |
| GET | `/internal/admin/keys` | `admin` scope | List all API keys |
| DELETE | `/internal/admin/keys/{id}` | `admin` scope | Revoke an API key |

## Authentication

Pass your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: hw_abc123..." http://localhost:8000/internal/trust/lookup \
  -d '{"name": "requests", "registry": "pypi"}'
```

## Architecture

```
Client → FastAPI (auth + rate limit) → DB Gate → PgBouncer → TimescaleDB
                                              ↗
Celery Worker → Crawlers → Trust Calculator →
```

The **Database Gate** (`src/core/db_gate.py`) provides:
- Connection pool management with overflow limits
- Statement and lock timeouts (prevent runaway queries)
- Circuit breaker pattern (stops cascading failures)
- Read/write routing (ready for read replicas)
- Health check endpoint with pool statistics

## Configuration

All configuration is via environment variables. See `.env.example` for the full list.

## Development

```bash
# Run tests
docker compose exec api pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## Free Deployment Options

### Render (Recommended)

One-click deploy using the included `render.yaml` blueprint:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

This provisions the API, worker, PostgreSQL, and Redis automatically.

### Railway

1. Create a new project on [railway.app](https://railway.app)
2. Add PostgreSQL and Redis from the dashboard
3. Connect your GitHub repo — Railway detects `railway.toml` automatically
4. Set environment variables from `.env.example`

### Self-hosted (Oracle Cloud Free Tier)

Oracle offers 2 free ARM VMs with 24GB RAM — enough to run the full Docker Compose stack:

```bash
ssh your-oracle-vm
git clone https://github.com/your-org/halwall.git
cd halwall
cp .env.example .env
# edit .env
docker compose up -d
```

## License

MIT — see [LICENSE](LICENSE).
