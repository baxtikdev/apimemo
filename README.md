# apimemo

**Automatic HTTP request logging for Python.** Records every outgoing API call to your database — zero config, batch-buffered, production-ready.

[![PyPI version](https://img.shields.io/pypi/v/apimemo.svg)](https://pypi.org/project/apimemo/)
[![Python versions](https://img.shields.io/pypi/pyversions/apimemo.svg)](https://pypi.org/project/apimemo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## Why apimemo?

Most applications make dozens of outgoing HTTP requests — to payment gateways, notification services, third-party APIs. When something goes wrong, you need answers: *What did we send? What came back? How long did it take?*

**apimemo** wraps your HTTP client (`httpx` or `requests`) and silently logs every request to your database. No manual logging. No code changes to every call site. Just plug in and see everything in your admin panel.

### Key Features

- **Zero-effort logging** — wrap your HTTP client once, every request is captured automatically
- **Batch-buffered writes** — logs are collected in memory and flushed in configurable batches to minimize database overhead
- **Thread-safe** — safe for multi-threaded applications with proper locking and daemon timers
- **Framework-native** — works with your existing ORM and migration tool, no separate database needed
- **Admin panel included** — Django Admin and starlette-admin (FastAPI) views out of the box
- **Configurable filtering** — ignore health checks, internal services, or specific paths with glob patterns
- **Body truncation** — automatically truncates large request/response bodies to keep your database lean
- **Graceful shutdown** — `atexit` hook ensures no logs are lost when your process exits

## Installation

```bash
pip install apimemo[django]        # Django + httpx
pip install apimemo[sqlalchemy]    # FastAPI + SQLAlchemy (async)
pip install apimemo[tortoise]      # FastAPI + Tortoise ORM
pip install apimemo[httpx]         # httpx interceptor only (bring your own storage)
pip install apimemo[requests]      # requests interceptor only
pip install apimemo[fastapi-admin] # starlette-admin panel for FastAPI
pip install apimemo[all]           # everything
```

## Quick Start

### Django

Add `"apimemo"` to your installed apps and run migrations — that's it.

```python
# settings.py
INSTALLED_APPS = [
    "apimemo",
    ...
]
```

```bash
python manage.py migrate
```

```python
# anywhere in your code
from apimemo.integrations.django import DjangoIntegration

integration = DjangoIntegration()
client = integration.get_client()

resp = client.get("https://api.stripe.com/v1/charges")
# → automatically logged to api_logs table
# → visible at /admin/apimemo/apilog/
```

### FastAPI + SQLAlchemy

```python
from sqlalchemy.ext.asyncio import create_async_engine
from apimemo.integrations.sqlalchemy import SqlAlchemyIntegration, ApiLogMixin

# 1. Define your model with the mixin
class ApiLog(Base, ApiLogMixin):
    __tablename__ = "api_logs"

# 2. Generate & apply migration
#    alembic revision --autogenerate -m "add api_logs"
#    alembic upgrade head

# 3. Create integration
engine = create_async_engine("postgresql+asyncpg://...")
integration = SqlAlchemyIntegration(engine)

# 4. Use the logged client
client = integration.get_async_client()
resp = await client.get("https://api.example.com/users")

# 5. (Optional) Mount admin panel
#    pip install apimemo[fastapi-admin]
integration.mount_admin(app)
```

### FastAPI + Tortoise ORM

```python
# tortoise config
TORTOISE_ORM = {
    "apps": {
        "apimemo": {
            "models": ["apimemo.integrations.tortoise"],
            "default_connection": "default",
        }
    }
}
# aerich migrate && aerich upgrade

from apimemo.integrations.tortoise import TortoiseIntegration

integration = TortoiseIntegration()
client = integration.get_async_client()
resp = await client.get("https://api.example.com/users")
```

### Using `requests` instead of `httpx`

Every integration also provides a `get_session()` method that returns a `requests.Session`:

```python
session = integration.get_session()
resp = session.post("https://api.example.com/webhook", json={"event": "test"})
```

## Configuration

```python
from apimemo import configure

configure(
    enabled=True,              # kill switch — disable all logging
    max_body_size=10240,       # truncate bodies larger than 10KB
    batch_size=50,             # flush after collecting 50 entries
    flush_interval=5.0,        # or flush every 5 seconds, whichever comes first
    ignore_hosts=("localhost", "*.internal.io"),  # skip these hosts (glob patterns)
    ignore_paths=("/health", "/metrics*"),         # skip these paths (glob patterns)
    log_request_body=True,     # capture request body
    log_response_body=True,    # capture response body
    log_headers=False,         # disabled by default — headers may contain auth tokens
)
```

Configuration is **incremental** — calling `configure(log_headers=True)` preserves all other settings. Call `configure()` with no arguments to reset to defaults.

## What Gets Logged

Every outgoing HTTP request produces a row in `api_logs`:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `method` | VARCHAR(10) | `GET`, `POST`, `PUT`, `DELETE`, etc. |
| `url` | TEXT | Full request URL |
| `host` | VARCHAR(255) | Target hostname (indexed) |
| `path` | VARCHAR(2048) | URL path |
| `status_code` | INTEGER | Response status code, `0` if request failed (indexed) |
| `request_headers` | TEXT | JSON-encoded request headers (if enabled) |
| `request_body` | TEXT | Request body (truncated to `max_body_size`) |
| `response_headers` | TEXT | JSON-encoded response headers (if enabled) |
| `response_body` | TEXT | Response body (truncated to `max_body_size`) |
| `duration_ms` | FLOAT | Request duration in milliseconds |
| `error` | TEXT | Exception message if request failed |
| `created_at` | DATETIME | Timestamp in UTC (indexed) |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐     ┌──────────┐
│ httpx/       │────▶│  LogBuffer   │────▶│  _flush() │────▶│ Database │
│ requests     │     │ (thread-safe │     │ (batch    │     │          │
│ interceptor  │     │  in-memory)  │     │  insert)  │     │          │
└─────────────┘     └──────────────┘     └───────────┘     └──────────┘
                     ▲ batch_size trigger
                     ▲ timer trigger (flush_interval)
                     ▲ atexit trigger
```

- **Interceptors** wrap httpx transports and requests sessions to capture request/response data
- **LogBuffer** collects entries in a thread-safe list and flushes on batch size, timer, or process exit
- **Integrations** provide the `_flush()` implementation specific to each ORM (SQLAlchemy async, Tortoise bulk_create, Django raw SQL)

## Supported Frameworks

| Framework | ORM | Migration Tool | Admin Panel |
|-----------|-----|---------------|-------------|
| Django | Django ORM | `manage.py migrate` | Django Admin |
| FastAPI | SQLAlchemy 2.0 (async) | Alembic `--autogenerate` | starlette-admin |
| FastAPI | Tortoise ORM | Aerich | — |
| Any | — | — | — (bring your own storage) |

## License

MIT
