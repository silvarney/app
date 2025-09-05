-- Script de inicialização do PostgreSQL
-- Este script é executado automaticamente pelo PostgreSQL na inicialização
-- As variáveis POSTGRES_DB, POSTGRES_USER e POSTGRES_PASSWORD são definidas pelo docker-compose.yml

-- Criar usuário se não existir
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = current_setting('POSTGRES_USER')) THEN
      
      EXECUTE format('CREATE USER %I WITH PASSWORD %L CREATEDB',
                     current_setting('POSTGRES_USER'),
                     current_setting('POSTGRES_PASSWORD'));
   END IF;
END
$do$;

-- Criar banco se não existir
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = current_setting('POSTGRES_DB')) THEN
      EXECUTE format('CREATE DATABASE %I OWNER %I',
                     current_setting('POSTGRES_DB'),
                     current_setting('POSTGRES_USER'));
   END IF;
END
$do$;

-- Garantir privilégios no banco
DO
$do$
BEGIN
   EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I',
                  current_setting('POSTGRES_DB'),
                  current_setting('POSTGRES_USER'));
END
$do$;