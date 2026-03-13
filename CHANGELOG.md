# Changelog

## v0.1.0 (2026-03-13)

Initial release.

### Features
- **httpx interceptor** — sync (`ApimemoTransport`) and async (`AsyncApimemoTransport`) transport wrappers
- **requests interceptor** — `ApimemoSession` drop-in replacement for `requests.Session`
- **Django integration** — `INSTALLED_APPS = ["apimemo"]`, auto migration, Django Admin panel (read-only, filterable)
- **SQLAlchemy integration** — `ApiLogMixin` for user-controlled model, Alembic `--autogenerate` support, optional starlette-admin
- **Tortoise ORM integration** — full model with Aerich migration support, `bulk_create` batch writes
- **Batch buffering** — thread-safe `LogBuffer` with configurable batch size, flush interval, and `atexit` hook
- **Configuration** — frozen dataclass config with `should_ignore()` glob filtering, incremental `configure()` that merges with previous values
- **Base integration class** — shared `get_client()`, `get_async_client()`, `get_session()`, `stop()` across all backends
