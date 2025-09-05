-- Script de inicialização do PostgreSQL
-- Este script garante que o usuário e banco sejam criados corretamente

-- Criar o usuário se não existir
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'saas_user') THEN

      CREATE ROLE saas_user LOGIN PASSWORD 'saas_password_2024';
   END IF;
END
$do$;

-- Criar o banco de dados se não existir
SELECT 'CREATE DATABASE saas_db OWNER saas_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'saas_db')\gexec

-- Conceder privilégios ao usuário
GRANT ALL PRIVILEGES ON DATABASE saas_db TO saas_user;
ALTER USER saas_user CREATEDB;