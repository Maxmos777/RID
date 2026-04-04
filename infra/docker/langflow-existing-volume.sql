-- Legado / DBA-only: preferir (com backend e .env):
--   docker compose run --rm langflow-pg-bootstrap
--   ou: cd backend && uv run python manage.py ensure_langflow_schema
--
-- Aplicar SQL directo só quando não há imagem Django disponível:
--   docker exec -i rid-db psql -U rid -d rid < infra/docker/langflow-existing-volume.sql

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'langflow') THEN
    CREATE ROLE langflow WITH LOGIN PASSWORD 'langflow';
  END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS langflow AUTHORIZATION langflow;
GRANT CONNECT ON DATABASE rid TO langflow;
ALTER ROLE langflow IN DATABASE rid SET search_path TO langflow, public;
REVOKE ALL ON SCHEMA langflow FROM PUBLIC;
GRANT USAGE ON SCHEMA langflow TO langflow;
ALTER DEFAULT PRIVILEGES FOR ROLE langflow IN SCHEMA langflow GRANT ALL ON TABLES TO langflow;
ALTER DEFAULT PRIVILEGES FOR ROLE langflow IN SCHEMA langflow GRANT ALL ON SEQUENCES TO langflow;
