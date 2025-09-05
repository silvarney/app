# Configuração do Banco de Dados PostgreSQL

## Processo de Inicialização

Este projeto utiliza PostgreSQL como banco de dados principal com um processo robusto de inicialização que garante:

### 1. Criação Automática do Usuário e Banco

O script `postgres-init/init-db.sql` é executado automaticamente na primeira inicialização do container PostgreSQL e:

- **Usa variáveis de ambiente**: Utiliza `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB` do docker-compose.yml
- Cria o usuário dinamicamente baseado na variável `POSTGRES_USER`
- Cria o banco de dados dinamicamente baseado na variável `POSTGRES_DB`
- Concede privilégios necessários ao usuário
- Permite que o usuário crie bancos de dados (necessário para testes)
- **Evita hardcoding**: Não usa valores fixos, garantindo flexibilidade

### 2. Healthcheck e Dependências

O `docker-compose.yml` está configurado com:

- **Healthcheck do PostgreSQL**: Verifica se o banco está pronto para conexões
- **Dependências condicionais**: O serviço web só inicia após o PostgreSQL estar saudável
- **Timeout adequado**: 30 segundos de período inicial + verificações a cada 10 segundos

### 3. Entrypoint Melhorado

O `entrypoint.sh` implementa:

- Verificação de conectividade com netcat
- Aguardo adicional de 5 segundos para inicialização completa
- Teste de conexão Django antes das migrações
- Execução segura das migrações

## Variáveis de Ambiente

As seguintes variáveis no `.env` controlam a configuração do banco:

```env
DB_NAME=saas_db
DB_USER=saas_user
DB_PASSWORD=saas_password_2024
DB_HOST=postgres
DB_PORT=5432
DATABASE_URL=postgresql://saas_user:saas_password_2024@postgres:5432/saas_db
```

## Comandos Úteis

### Reiniciar apenas o banco de dados:
```bash
docker-compose down postgres
docker volume rm saas_postgres_data  # Remove dados persistentes
docker-compose up postgres
```

### Verificar logs do PostgreSQL:
```bash
docker-compose logs postgres
```

### Conectar ao banco via psql:
```bash
docker-compose exec postgres psql -U saas_user -d saas_db
```

## Solução de Problemas

### Erro de Autenticação
Se houver erros de autenticação:
1. Verifique se as variáveis no `.env` estão corretas
2. Remova o volume do PostgreSQL: `docker volume rm saas_postgres_data`
3. Reinicie os containers: `docker-compose up --build`

### Banco não Inicializa
Se o banco não inicializar corretamente:
1. Verifique os logs: `docker-compose logs postgres`
2. Certifique-se de que a porta 5439 não está em uso
3. Verifique se o script `init-db.sql` tem permissões corretas

### Migrações Falham
Se as migrações Django falharem:
1. O entrypoint agora testa a conexão antes das migrações
2. Verifique os logs do serviço web: `docker-compose logs web`
3. Execute migrações manualmente: `docker-compose exec web python manage.py migrate`