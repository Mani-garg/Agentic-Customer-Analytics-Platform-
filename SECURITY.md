# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability or bypass in the SQL Guard, agent boundaries, or API endpoints, please report it privately to the maintainers rather than opening a public issue.

## Security Architecture Principles

This platform adheres to strict defense-in-depth principles:

1. **SQL Guardrails**:
   - The analytics agent is **never** permitted direct, unrestricted SQL execution.
   - All agent queries pass through AST parsing (`sqlglot`) to enforce single-statement read-only `SELECT` queries.
   - Strict table allow-listing rejects access to internal schemas, sqlite_master, pg_catalog, and sensitive configuration.
   - Multi-statement queries, DDL, DML, CTE bypasses, and unauthorized functions are rejected before database dispatch.
2. **Least Privilege Database Connections**:
   - The agent database connection role is strictly read-only at the database engine level.
   - Write permissions (INSERT, UPDATE, DELETE, DROP, ALTER) are denied at the database role level.
3. **Execution Limits**:
   - Query length limit (default: 1,000 characters).
   - Statement execution timeout (default: 5,000 ms).
   - Maximum result rows bounded server-side and client-side (default: 100 rows).
4. **Data Minimization & Privacy**:
   - Identifiers and sensitive attributes are masked or excluded from LLM context.
   - Logging redaction prevents leaking secrets, credentials, or customer PII into logs.
