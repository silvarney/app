-- Comandos SQL para verificação e manipulação do PostgreSQL durante migração para UUID

-- Conectar ao PostgreSQL
-- psql -U seu_usuario -d seu_banco

-- Listar todas as tabelas do banco de dados
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verificar a estrutura de uma tabela específica
\d nome_da_tabela

-- Verificar se uma coluna é UUID
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'nome_da_tabela' 
  AND column_name = 'id';

-- Backup de uma tabela específica antes de alterá-la
CREATE TABLE nome_da_tabela_backup AS 
SELECT * FROM nome_da_tabela;

-- Converter uma coluna para UUID (exemplo)
-- 1. Adicionar uma nova coluna UUID
ALTER TABLE nome_da_tabela ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();

-- 2. Preencher a coluna com valores UUID
UPDATE nome_da_tabela SET uuid_id = gen_random_uuid();

-- 3. Remover a antiga chave primária
ALTER TABLE nome_da_tabela DROP CONSTRAINT nome_da_tabela_pkey;

-- 4. Fazer da nova coluna a chave primária
ALTER TABLE nome_da_tabela ADD PRIMARY KEY (uuid_id);

-- 5. Remover a antiga coluna ID
ALTER TABLE nome_da_tabela DROP COLUMN id;

-- 6. Renomear a coluna UUID para id
ALTER TABLE nome_da_tabela RENAME COLUMN uuid_id TO id;

-- Verificar referências/chaves estrangeiras para uma tabela
SELECT
    tc.table_schema, 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
JOIN 
    information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN 
    information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE 
    tc.constraint_type = 'FOREIGN KEY' AND
    (tc.table_name = 'nome_da_tabela' OR ccu.table_name = 'nome_da_tabela');

-- Remover todas as chaves estrangeiras referenciando uma tabela
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT constraint_name, table_name FROM information_schema.table_constraints
             WHERE constraint_type = 'FOREIGN KEY'
             AND table_schema = 'public'
             AND constraint_name IN (
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'nome_da_tabela'
             )
    LOOP
        EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT ' || r.constraint_name;
    END LOOP;
END $$;

-- Reconstruir banco de dados do zero
-- 1. Desconectar todos os clientes (em outro terminal como superusuário)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'seu_banco'
  AND pid <> pg_backend_pid();

-- 2. Dropar e recriar o banco
DROP DATABASE seu_banco;
CREATE DATABASE seu_banco WITH OWNER seu_usuario;
