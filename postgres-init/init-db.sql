-- Script de inicialização do PostgreSQL
-- Este script é executado automaticamente pelo PostgreSQL na inicialização
-- As variáveis POSTGRES_DB, POSTGRES_USER e POSTGRES_PASSWORD são definidas pelo docker-compose.yml
-- O PostgreSQL automaticamente cria o usuário e banco baseado nessas variáveis
-- Este script apenas garante privilégios adicionais

-- O PostgreSQL já criou o usuário e banco automaticamente
-- Apenas concedemos privilégios extras se necessário

-- Permitir que o usuário crie bancos de dados (necessário para testes Django)
ALTER USER "${POSTGRES_USER}" CREATEDB;

-- Garantir que o usuário tem todos os privilégios no banco
GRANT ALL PRIVILEGES ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_USER}";

-- Conectar ao banco criado e conceder privilégios no schema public
\c "${POSTGRES_DB}"
GRANT ALL ON SCHEMA public TO "${POSTGRES_USER}";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${POSTGRES_USER}";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "${POSTGRES_USER}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${POSTGRES_USER}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${POSTGRES_USER}";