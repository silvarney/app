# SaaS Project - Docker Deployment Guide

Este guia fornece instruções completas para executar o projeto SaaS usando Docker diretamente no host.

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Nginx Proxy Manager (para gerenciar domínios e SSL)
- Pelo menos 2GB de RAM disponível
- 10GB de espaço em disco

## 🚀 Início Rápido (Desenvolvimento)

### 1. Clone o repositório e configure o ambiente

```bash
git clone <seu-repositorio>
cd saas
cp .env.example .env.docker
```

### 2. Configure as variáveis de ambiente

Edite o arquivo `.env.docker` com suas configurações:

```bash
# Configurações essenciais
SECRET_KEY=sua-chave-secreta-super-segura-aqui
DB_PASSWORD=senha-segura-do-banco
ALLOWED_HOSTS=localhost,127.0.0.1,seu-dominio.com

# Email (configure conforme seu provedor)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
```

### 3. Execute o projeto

```bash
# Construir e executar todos os serviços
docker-compose up --build -d

# Verificar logs
docker-compose logs -f

# Acessar a aplicação
# http://localhost (via Nginx)
# http://localhost:8000 (direto no Django)
```

### 4. Comandos úteis

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker-compose down -v

# Executar comandos Django
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic

# Acessar shell do container
docker-compose exec web bash

# Ver logs de um serviço específico
docker-compose logs -f web
docker-compose logs -f db
```

## 🏭 Deploy em Produção no Host

### 1. Preparação do Servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configuração das Variáveis de Ambiente

1. Copie o arquivo `.env.example` para `.env.prod`
2. Configure as variáveis de ambiente:

```env
# Variáveis obrigatórias
SECRET_KEY=sua-chave-secreta-super-segura-de-producao
DB_PASSWORD=senha-muito-segura-do-banco-producao
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Configurações de email
EMAIL_HOST=smtp.seu-provedor.com
EMAIL_HOST_USER=noreply@seu-dominio.com
EMAIL_HOST_PASSWORD=senha-do-email

# Configurações de segurança (HTTPS)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Configuração para Nginx Proxy Manager
VIRTUAL_HOST=seu-dominio.com
VIRTUAL_PORT=8000
LETSENCRYPT_HOST=seu-dominio.com
LETSENCRYPT_EMAIL=seu-email@dominio.com

# Caminhos personalizados
DATA_PATH=/opt/saas-data

# Portas customizadas (opcional)
HTTP_PORT=80
HTTPS_PORT=443
```

### 3. Deploy da Aplicação

```bash
# Execute o docker-compose de produção
docker-compose -f docker-compose.prod.yml up -d

# Verifique se todos os serviços estão rodando
docker-compose -f docker-compose.prod.yml ps

# Acompanhe os logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Configuração no Nginx Proxy Manager

1. **Acesse o Nginx Proxy Manager**
2. **Adicione um novo Proxy Host:**
   - Domain Names: `seu-dominio.com`
   - Scheme: `http`
   - Forward Hostname/IP: `IP_DO_SEU_SERVIDOR`
   - Forward Port: `8000`
3. **Configure SSL:**
   - Aba "SSL"
   - Request a new SSL Certificate
   - Use Let's Encrypt
   - Email: seu-email@dominio.com
   - Aceite os termos
4. **Configurações avançadas:**
   - Aba "Advanced"
   - Adicione configurações personalizadas se necessário

### 4. Configuração de Backup

```bash
# Script de backup (salvar como backup.sh)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/saas"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
docker exec saas_db_prod pg_dump -U saas_user saas_db > $BACKUP_DIR/db_$DATE.sql

# Backup dos arquivos de media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /opt/saas-data media/

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

```bash
# Tornar executável e agendar no cron
chmod +x backup.sh
crontab -e
# Adicionar linha para backup diário às 2h da manhã:
0 2 * * * /opt/scripts/backup.sh
```

## 🔧 Estrutura do Projeto

```
saas/
├── Dockerfile                     # Imagem principal da aplicação
├── docker-compose.yml            # Configuração dos serviços
├── requirements.txt              # Dependências Python
├── entrypoint.sh                # Script de inicialização com verificações
├── .env                         # Variáveis de ambiente
├── .env.example                 # Template de variáveis
│   └── default.conf            # Configuração do servidor virtual
└── README-Docker.md            # Este arquivo
```

## 🐳 Serviços Docker

| Serviço | Porta | Descrição |
|---------|-------|----------|
| **nginx** | 80, 443 | Proxy reverso e servidor de arquivos estáticos |
| **web** | 8000 | Aplicação Django principal |
| **db** | 5432 | Banco de dados PostgreSQL |
| **redis** | 6379 | Cache e broker do Celery |
| **celery** | - | Worker para tarefas assíncronas |
| **celery-beat** | - | Agendador de tarefas |

## 🔍 Monitoramento e Logs

```bash
# Ver status de todos os containers
docker ps

# Monitorar recursos
docker stats

# Logs em tempo real (desenvolvimento)
docker-compose logs -f --tail=100

# Logs em tempo real (produção)
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Logs de um serviço específico (desenvolvimento)
docker-compose logs -f web

# Logs de um serviço específico (produção)
docker-compose -f docker-compose.prod.yml logs -f web

# Verificar saúde dos serviços (desenvolvimento)
docker-compose ps

# Verificar saúde dos serviços (produção)
docker-compose -f docker-compose.prod.yml ps
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco de dados**
   ```bash
   # Verificar se o PostgreSQL está rodando (desenvolvimento)
   docker-compose exec db pg_isready -U saas_user
   
   # Verificar se o PostgreSQL está rodando (produção)
   docker-compose -f docker-compose.prod.yml exec db pg_isready -U saas_user
   
   # Verificar logs do banco (produção)
   docker-compose -f docker-compose.prod.yml logs db
   ```

2. **Arquivos estáticos não carregam**
   ```bash
   # Recopilar arquivos estáticos (produção)
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   
   # Verificar permissões
   docker-compose -f docker-compose.prod.yml exec web ls -la /app/staticfiles/
   ```

3. **Celery não processa tarefas**
   ```bash
   # Verificar worker do Celery (produção)
   docker-compose -f docker-compose.prod.yml logs celery
   
   # Verificar conexão com Redis (produção)
   docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
   ```

4. **Problemas com Nginx Proxy Manager**
   ```bash
   # Verificar se a aplicação está acessível na porta 8000
   curl http://localhost:8000
   
   # Verificar configurações de proxy no NPM
   # Acessar interface web do Nginx Proxy Manager
   ```

5. **Erro de memória**
   ```bash
   # Verificar uso de recursos
   docker stats
   
   # Ajustar limites no docker-compose.prod.yml
   deploy:
     resources:
       limits:
         memory: 1G
   ```

### Comandos de Diagnóstico

```bash
# Verificar configuração do Docker
docker info

# Verificar redes
docker network ls
docker network inspect saas_saas_network

# Verificar volumes
docker volume ls
docker volume inspect saas_postgres_data

# Testar conectividade entre containers (desenvolvimento)
docker-compose exec web ping db
docker-compose exec web ping redis

# Testar conectividade entre containers (produção)
docker-compose -f docker-compose.prod.yml exec web ping db
docker-compose -f docker-compose.prod.yml exec web ping redis

# Verificar se a aplicação responde
curl -I http://localhost:8000/health/
```

## 🔐 Segurança

### Checklist de Segurança

- [ ] Alterar todas as senhas padrão
- [ ] Configurar HTTPS com certificados válidos
- [ ] Configurar firewall (apenas portas 80, 443, 22)
- [ ] Habilitar logs de auditoria
- [ ] Configurar backup automático
- [ ] Atualizar regularmente as imagens Docker
- [ ] Monitorar logs de segurança
- [ ] Configurar rate limiting no Nginx

### Variáveis Sensíveis

Nunca commite no Git:
- `SECRET_KEY`
- `DB_PASSWORD`
- `EMAIL_HOST_PASSWORD`
- Certificados SSL
- Tokens de API

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `docker-compose logs`
2. Consulte a documentação do Django
3. Abra uma issue no repositório

---

**Nota**: Este projeto está configurado para produção. Certifique-se de revisar todas as configurações de segurança antes do deploy.