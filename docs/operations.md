# Operations and Deployment Guide

## 1. Local and Production Configuration

The application is configured through environment variables loaded centrally by Pydantic Settings (`src/customer_analytics/config.py`).

| Variable | Default Value | Description | Sensitivity |
|:---|:---|:---|:---:|
| `APP_ENV` | `development` | Runtime environment (`development`, `testing`, `production`) | Low |
| `API_HOST` | `0.0.0.0` | API bind address | Low |
| `API_PORT` | `8000` | API bind port | Low |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | Low |
| `LOG_JSON` | `false` | Emit structured JSON logs when set to `true` | Low |
| `DATABASE_URL` | `sqlite:///./data/analytics.db` | Primary application read/write database connection | **High** |
| `AGENT_DATABASE_URL` | `sqlite:///./data/analytics.db` | Least-privilege read-only connection for Agent queries | **High** |
| `SPARK_ENABLED` | `false` | Enable PySpark batch execution (requires Java 8/11/17) | Low |
| `LLM_PROVIDER` | `none` | LLM provider selection (`none`, `mock`, `openai`, `anthropic`) | Low |
| `LLM_API_KEY` | *(empty)* | Optional API key for language model | **High** |
| `SQL_MAX_ROWS` | `100` | Maximum rows returned by agent queries | Medium |
| `SQL_STATEMENT_TIMEOUT_MS` | `5000` | Database query timeout in milliseconds | Medium |

---

## 2. Health & Readiness Checking

Docker Compose and container orchestrators should monitor:
- **Liveness Probe**: `GET /health/live` (confirms process is active and event loop is responsive).
- **Readiness Probe**: `GET /health/ready` (confirms database connectivity and model storage availability).

---

## 3. Containerized Deployment with Docker Compose

### 3.1 Start Services
```bash
docker compose up -d
```
This starts:
1. `db`: PostgreSQL 16 on `localhost:5432` with pre-configured `analytics_app` and `analytics_readonly` roles.
2. `api`: Containerized FastAPI application running as non-root user `appuser` on `localhost:8000`.

### 3.2 Inspect Logs & Status
```bash
docker compose ps
docker compose logs -f api
```

### 3.3 Stop Services
```bash
docker compose down
```

---

## 4. Failure Recovery & Operational Safeguards

1. **Missing LLM Key**: The platform starts cleanly without an LLM key. All deterministic analytics endpoints, ML inference, and the agent's deterministic fallback query router remain 100% operational.
2. **Missing Java / PySpark**: When Java or PySpark is absent, the system detects this at startup and activates the vectorized in-memory analytics engine without crashing.
3. **Database Timeout / Error**: If a query times out or the database drops, the platform catches the failure, logs the correlation ID, and returns a sanitized `503 Service Unavailable` response. Credentials and internal engine errors are never leaked to clients.
