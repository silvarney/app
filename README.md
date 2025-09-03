# Sistema SaaS Django

Um sistema SaaS completo desenvolvido em Django com funcionalidades de multi-tenancy, gerenciamento de usuários, permissões e painéis administrativos.

## 🚀 Funcionalidades

- **Multi-tenancy**: Suporte a múltiplas contas/organizações
- **Autenticação**: Login com email, autenticação social (Google)
- **Gerenciamento de Usuários**: Diferentes tipos de usuário (Admin, Gerente, Usuário Comum, Convidado)
- **Permissões**: Sistema granular de permissões por usuário
- **Painéis**: Interface administrativa e painel do usuário
- **API REST**: Endpoints para integração
- **Pagamentos**: Integração preparada para sistemas de pagamento
- **Tarefas**: Sistema de gerenciamento de tarefas
- **Domínios**: Gerenciamento de domínios personalizados

## 📋 Pré-requisitos

- Python 3.8+
- Node.js 16+ (para Tailwind CSS)
- Git

## 🛠️ Instalação e Execução

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd saas
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências Python

```bash
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-allauth
pip install Pillow
pip install cryptography
```

### 4. Instale as dependências Node.js

```bash
npm install
```

### 5. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# Configurações do Google OAuth (opcional)
GOOGLE_OAUTH2_CLIENT_ID=seu-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=seu-client-secret
```

### 6. Execute as migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crie um superusuário

```bash
python manage.py createsuperuser
```

### 8. Compile o CSS (Tailwind)

```bash
npm run build-css
```

### 9. Execute o servidor

```bash
python manage.py runserver
```

O sistema estará disponível em: `http://127.0.0.1:8000/`

## 🐳 Execução com Docker

### Pré-requisitos Docker

- Docker
- Docker Compose

### 1. Crie o arquivo Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto:

```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt package*.json ./

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependências Node.js
RUN npm install

# Copiar código da aplicação
COPY . .

# Compilar CSS
RUN npm run build-css

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE 8000

# Comando para executar a aplicação
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 2. Crie o arquivo requirements.txt

```bash
echo "Django>=5.0,<6.0" > requirements.txt
echo "djangorestframework>=3.14" >> requirements.txt
echo "djangorestframework-simplejwt>=5.0" >> requirements.txt
echo "django-allauth>=0.50" >> requirements.txt
echo "Pillow>=9.0" >> requirements.txt
echo "cryptography>=3.0" >> requirements.txt
```

### 3. Crie o arquivo docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - DEBUG=1
      - SECRET_KEY=docker-secret-key-change-in-production
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=saas_db
      - POSTGRES_USER=saas_user
      - POSTGRES_PASSWORD=saas_password
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 4. Execute com Docker Compose

```bash
# Construir e executar os containers
docker-compose up --build

# Executar em background
docker-compose up -d --build

# Executar migrações (primeira vez)
docker-compose exec web python manage.py migrate

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Parar os containers
docker-compose down
```

O sistema estará disponível em: `http://localhost:8000/`

## 📁 Estrutura do Projeto

```
saas/
├── accounts/          # Gerenciamento de contas/organizações
├── admin_panel/       # Painel administrativo
├── api/              # APIs REST
├── domains/          # Gerenciamento de domínios
├── payments/         # Sistema de pagamentos
├── permissions/      # Sistema de permissões
├── saas_project/     # Configurações do Django
├── static/           # Arquivos estáticos (CSS, JS)
├── tasks/            # Sistema de tarefas
├── templates/        # Templates HTML
├── user_panel/       # Painel do usuário
├── users/            # Gerenciamento de usuários
├── manage.py         # Script de gerenciamento Django
├── package.json      # Dependências Node.js
└── requirements.txt  # Dependências Python
```

## 🔧 Comandos Úteis

```bash
# Executar testes
python manage.py test

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Compilar CSS do Tailwind
npm run build-css

# Modo de desenvolvimento do Tailwind (watch)
npm run dev-css
```

## 🌐 URLs Principais

- **Home**: `http://127.0.0.1:8000/`
- **Login**: `http://127.0.0.1:8000/auth/login/`
- **Admin Django**: `http://127.0.0.1:8000/admin/`
- **Painel Admin**: `http://127.0.0.1:8000/admin-panel/`
- **Painel Usuário**: `http://127.0.0.1:8000/user-panel/`
- **API**: `http://127.0.0.1:8000/api/`

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte, entre em contato através do email: suporte@exemplo.com

---

**Desenvolvido com ❤️ usando Django e Tailwind CSS**