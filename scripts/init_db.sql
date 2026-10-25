-- ==============================================================================
-- PostgreSQL Least-Privilege Role Setup for Customer Analytics Platform
-- ==============================================================================

-- 1. Create standard application role (read/write on application schema)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_app') THEN
      CREATE ROLE analytics_app WITH LOGIN PASSWORD 'app_secret_pass';
   END IF;
END
$do$;

-- 2. Create restricted read-only agent role
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_readonly') THEN
      CREATE ROLE analytics_readonly WITH LOGIN PASSWORD 'ro_secret_pass';
   END IF;
END
$do$;

-- Revoke default public schema creation
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO analytics_app;
GRANT USAGE ON SCHEMA public TO analytics_readonly;

-- Grant standard permissions to application role
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO analytics_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO analytics_app;

-- Grant strictly SELECT permissions to agent role
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_readonly;

-- Ensure read-only role cannot create or modify objects
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
