# Contributing to HalWall

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

1. Fork and clone the repo
2. Start local services: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
3. Run migrations: `docker compose exec api alembic upgrade head`
4. Create an admin key: `docker compose exec api python -m scripts.create_admin_key`

## Code Style

- **Formatter**: `black` (line length 100)
- **Import sorting**: `isort` (profile=black)
- **Type checking**: `mypy` (strict mode encouraged)
- All new code should have type annotations

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure `pytest` passes
4. Run `black` and `isort` before committing
5. Write a clear PR description explaining what and why

## Database Changes

- All schema changes require an Alembic migration
- Run `alembic revision --autogenerate -m "description"` to generate
- Review the generated migration before committing
- Migrations must be reversible (implement `downgrade()`)

## Security

If you discover a security vulnerability, **do not open a public issue**. 
Email security@halwall.dev (or open a private advisory on GitHub) with details.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
