# 🚀 Guia de Deploy em Produção - SaaS Project

Este guia fornece instruções **passo a passo** para fazer o deploy do projeto SaaS em produção usando Docker e Nginx Proxy Manager.

## 📋 Pré-requisitos

### No Servidor
- Ubuntu 20.04+ ou CentOS 8+ (recomendado)
- Docker Engine 20.10+
- Docker Compose 2.0+
- Pelo menos 2GB de RAM
- 20GB de espaço em disco
- Nginx Proxy Manager instalado e configurado
- Domínio apontando para o servidor

### Verificar Instalações
```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar se o Docker está rodando
sudo systemctl status docker
```

## 🔧 Passo 1: Preparação do Servidor

### 1.1 Atualizar o Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Instalar Docker (se não estiver instalado)
```bash
# Remover versões antigas
sudo apt remove docker docker-engine docker.io containerd runc

# Instalar dependências
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### 1.3 Criar Diretórios do Projeto
```bash
# Criar diretório principal
sudo mkdir -p /opt/saas-project
sudo chown $USER:$USER /opt/saas-project
cd /opt/saas-project

# Criar diretórios para dados
mkdir -p logs backups
```

## 📦 Passo 2: Deploy da Aplicação

### 2.1 Clonar o Repositório
```bash
cd /opt/saas-project
git clone <URL_DO_SEU_REPOSITORIO> .

# Ou fazer upload dos arquivos via SCP/SFTP
```

### 2.2 Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.prod .env.prod.local

# Editar configurações (IMPORTANTE!)
nano .env.prod.local
```

**Configurações OBRIGATÓRIAS no .env.prod.local:**
```env
# ALTERE ESTAS CONFIGURAÇÕES!
DJANGO_SECRET_KEY=SUA_CHAVE_SECRETA_MUITO_FORTE_AQUI_50_CARACTERES
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
SITE_URL=https://seu-dominio.com

# Banco de dados
DB_PASSWORD=SENHA_MUITO_FORTE_DO_BANCO

# Email
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com

# JWT
JWT_SECRET_KEY=CHAVE_JWT_MUITO_FORTE

# Nginx Proxy Manager
VIRTUAL_HOST=seu-dominio.com
LETSENCRYPT_HOST=seu-dominio.com
LETSENCRYPT_EMAIL=seu-email@dominio.com
```

### 2.3 Construir e Executar os Containers
```bash
# Construir as imagens
docker-compose -f docker-compose.prod.yml build

# Executar em background
docker-compose -f docker-compose.prod.yml up -d

# Verificar se todos os serviços estão rodando
docker-compose -f docker-compose.prod.yml ps
```

### 2.4 Executar Migrações e Configurações Iniciais
```bash
# Aguardar os serviços iniciarem (30-60 segundos)
sleep 60

# Executar migrações
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verificar se a aplicação está respondendo
curl -I http://localhost:8000/health/
```

## 🌐 Passo 3: Configurar Nginx Proxy Manager

### 3.1 Acessar o Nginx Proxy Manager
1. Acesse a interface web do NPM (geralmente na porta 81)
2. Faça login com suas credenciais

### 3.2 Adicionar Proxy Host
1. **Vá para "Proxy Hosts"**
2. **Clique em "Add Proxy Host"**
3. **Configure a aba "Details":**
   - **Domain Names:** `seu-dominio.com`
   - **Scheme:** `http`
   - **Forward Hostname/IP:** `IP_DO_SEU_SERVIDOR` (ou `localhost` se NPM estiver no mesmo servidor)
   - **Forward Port:** `8000`
   - **Cache Assets:** ✅ (marcado)
   - **Block Common Exploits:** ✅ (marcado)
   - **Websockets Support:** ✅ (marcado)

4. **Configure a aba "SSL":**
   - **SSL Certificate:** `Request a new SSL Certificate`
   - **Force SSL:** ✅ (marcado)
   - **HTTP/2 Support:** ✅ (marcado)
   - **HSTS Enabled:** ✅ (marcado)
   - **Use Let's Encrypt:** ✅ (marcado)
   - **Email Address:** `seu-email@dominio.com`
   - **I Agree to the Let's Encrypt Terms of Service:** ✅ (marcado)

5. **Configure a aba "Advanced" (opcional):**
```nginx
# Configurações adicionais para melhor performance
client_max_body_size 100M;
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

# Headers de segurança
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
```

6. **Clique em "Save"**

### 3.3 Testar a Configuração
```bash
# Testar HTTP (deve redirecionar para HTTPS)
curl -I http://seu-dominio.com

# Testar HTTPS
curl -I https://seu-dominio.com

# Verificar certificado SSL
echo | openssl s_client -servername seu-dominio.com -connect seu-dominio.com:443 2>/dev/null | openssl x509 -noout -dates
```

## 🔍 Passo 4: Verificação e Testes

### 4.1 Verificar Serviços
```bash
# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs da aplicação
docker-compose -f docker-compose.prod.yml logs -f web

# Verificar saúde dos serviços
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### 4.2 Testes Funcionais
1. **Acesse:** `https://seu-dominio.com`
2. **Teste o admin:** `https://seu-dominio.com/admin`
3. **Teste a API:** `https://seu-dominio.com/api/`
4. **Verifique SSL:** Certificado deve estar válido

## 🔄 Passo 5: Configurar Backups Automáticos

### 5.1 Script de Backup
```bash
# Criar script de backup
sudo nano /opt/saas-project/backup.sh
```

**Conteúdo do backup.sh:**
```bash
#!/bin/bash

# Configurações
PROJECT_DIR="/opt/saas-project"
BACKUP_DIR="$PROJECT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec -T postgres pg_dump -U saas_user saas_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos de media
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C $PROJECT_DIR media/

# Remover backups antigos
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup concluído: $DATE"
```

### 5.2 Configurar Cron
```bash
# Tornar executável
chmod +x /opt/saas-project/backup.sh

# Adicionar ao cron (backup diário às 2h)
crontab -e

# Adicionar esta linha:
0 2 * * * /opt/saas-project/backup.sh >> /opt/saas-project/logs/backup.log 2>&1
```

## 🔧 Comandos Úteis para Manutenção

### Logs e Monitoramento
```bash
# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs de um serviço específico
docker-compose -f docker-compose.prod.yml logs -f web

# Verificar uso de recursos
docker stats

# Verificar espaço em disco
df -h
docker system df
```

### Atualizações
```bash
# Parar serviços
docker-compose -f docker-compose.prod.yml down

# Atualizar código
git pull origin main

# Reconstruir e reiniciar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Executar migrações se necessário
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Limpeza
```bash
# Remover containers parados
docker container prune -f

# Remover imagens não utilizadas
docker image prune -f

# Remover volumes não utilizados (CUIDADO!)
docker volume prune -f
```

## 🚨 Troubleshooting

### Problema: Aplicação não responde
```bash
# Verificar se os containers estão rodando
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
docker-compose -f docker-compose.prod.yml logs web

# Reiniciar serviços
docker-compose -f docker-compose.prod.yml restart
```

### Problema: Erro de SSL
1. Verificar se o domínio está apontando corretamente
2. Verificar configurações no Nginx Proxy Manager
3. Verificar se as portas 80 e 443 estão abertas
4. Tentar renovar o certificado SSL no NPM

### Problema: Banco de dados não conecta
```bash
# Verificar se o PostgreSQL está rodando
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U saas_user

# Verificar logs do banco
docker-compose -f docker-compose.prod.yml logs postgres

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml exec web env | grep DB_
```

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker-compose -f docker-compose.prod.yml logs`
2. Consulte a documentação do Django
3. Verifique as configurações do Nginx Proxy Manager
4. Entre em contato com o suporte técnico

---

**✅ Checklist Final:**
- [ ] Servidor preparado e Docker instalado
- [ ] Código clonado e configurado
- [ ] Variáveis de ambiente configuradas
- [ ] Containers rodando sem erros
- [ ] Nginx Proxy Manager configurado
- [ ] SSL funcionando
- [ ] Backups configurados
- [ ] Testes funcionais realizados

**🎉 Parabéns! Sua aplicação está em produção!**