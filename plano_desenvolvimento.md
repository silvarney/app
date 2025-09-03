# Plano de Desenvolvimento - Sistema SaaS Django

## Visão Geral do Projeto
Sistema SaaS para gerenciamento de conteúdos que serão consumidos via API por sites desenvolvidos em Astro. O sistema terá dois ambientes distintos: **Admin** e **Usuários**, com design responsivo mobile-first usando Tailwind CSS.

## Características Principais
- **Multi-tenant**: Usuários podem ter múltiplas contas e participar de outras contas
- **RBAC**: Sistema de permissões baseado em papéis personalizáveis por conta
- **API REST**: Para consumo por sites Astro
- **Pagamentos**: Integração com gateways de pagamento
- **Design**: Mobile-first, responsivo, clean e intuitivo

---

## FASE 1: Configuração Inicial do Projeto

### 1.1 Criação do Ambiente Virtual e Projeto Django
```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instalar Django e dependências básicas
pip install django djangorestframework python-decouple django-cors-headers
pip install djangorestframework-simplejwt
pip install celery redis
pip install pillow

# Criar projeto Django
django-admin startproject saas_project .
```

### 1.2 Configuração do Tailwind CSS
```bash
# Instalar Node.js e npm (se não tiver)
# Instalar Tailwind CSS
npm init -y
npm install -D tailwindcss @tailwindcss/forms @tailwindcss/typography
npx tailwindcss init

# Instalar django-tailwind (alternativa)
pip install django-tailwind[reload]
```

### 1.3 Estrutura de Apps Django
```bash
# Criar apps principais
python manage.py startapp users
python manage.py startapp accounts
python manage.py startapp permissions
python manage.py startapp domains
python manage.py startapp payments
python manage.py startapp api
python manage.py startapp admin_panel
python manage.py startapp user_panel
python manage.py startapp tasks
```

---

## FASE 2: Configuração Base do Django

### 2.1 Settings.py - Configurações Principais
```python
# Adicionar apps ao INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'tailwind',  # se usar django-tailwind
    
    # Local apps
    'users',
    'accounts',
    'permissions',
    'domains',
    'payments',
    'api',
    'admin_panel',
    'user_panel',
    'tasks',
]

# Configurar middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configurar DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Configurar JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

### 2.2 URLs Principais
```python
# saas_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Admin Django nativo
    path('admin/', include('admin_panel.urls')),  # Painel Admin customizado
    path('app/', include('user_panel.urls')),     # Painel Usuários
    path('api/v1/', include('api.urls')),         # API REST
    path('api/auth/', include('users.urls')),     # Autenticação
]
```

---

## FASE 3: Modelos de Dados

### 3.1 App Users - Modelo de Usuário Customizado
```python
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('blocked', 'Bloqueado'),
    ]
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

### 3.2 App Accounts - Contas/Organizações
```python
# accounts/models.py
from django.db import models
from django.conf import settings

class Account(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    cnpj = models.CharField(max_length=18, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class AccountMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('member', 'Membro'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'account']
```

### 3.3 App Permissions - Sistema RBAC
```python
# permissions/models.py
from django.db import models

class Permission(models.Model):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50)  # users, accounts, payments, etc.
    
class Role(models.Model):
    name = models.CharField(max_length=100)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
```

---

## FASE 4: Frontend - Configuração Tailwind CSS

### 4.1 Configuração do Tailwind
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
    './admin_panel/templates/**/*.html',
    './user_panel/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          900: '#111827',
        }
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### 4.2 Estrutura de Templates Base
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SaaS Platform{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <link href="{% static 'css/tailwind.css' %}" rel="stylesheet">
    
    <!-- Meta tags para mobile -->
    <meta name="theme-color" content="#3b82f6">
    <meta name="mobile-web-app-capable" content="yes">
    
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-50 font-sans antialiased">
    {% block content %}{% endblock %}
    
    <!-- Scripts -->
    <script src="{% static 'js/app.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

## FASE 5: Painel Administrativo

### 5.1 Estrutura do Admin Panel
```python
# admin_panel/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adicionar dados do dashboard
        return context
```

### 5.2 Template do Dashboard Admin
```html
<!-- admin_panel/templates/admin_panel/dashboard.html -->
{% extends 'admin_panel/base.html' %}

{% block content %}
<div class="min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform -translate-x-full lg:translate-x-0 transition-transform duration-200 ease-in-out" id="sidebar">
        <!-- Sidebar content -->
        <div class="flex flex-col h-full">
            <div class="flex items-center justify-center h-16 bg-primary-600">
                <h1 class="text-white text-xl font-bold">Admin Panel</h1>
            </div>
            
            <nav class="flex-1 px-4 py-6 space-y-2">
                <a href="#" class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100">
                    <span>Dashboard</span>
                </a>
                <a href="#" class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100">
                    <span>Usuários</span>
                </a>
                <a href="#" class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100">
                    <span>Contas</span>
                </a>
                <a href="#" class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100">
                    <span>Permissões</span>
                </a>
                <a href="#" class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100">
                    <span>Pagamentos</span>
                </a>
            </nav>
        </div>
    </div>
    
    <!-- Main content -->
    <div class="lg:ml-64">
        <!-- Top bar -->
        <header class="bg-white shadow-sm border-b border-gray-200">
            <div class="flex items-center justify-between px-4 py-4">
                <button class="lg:hidden" id="sidebar-toggle">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
                
                <div class="flex items-center space-x-4">
                    <span class="text-sm text-gray-700">Olá, {{ user.first_name|default:user.username }}</span>
                    <a href="{% url 'logout' %}" class="text-sm text-red-600 hover:text-red-800">Sair</a>
                </div>
            </div>
        </header>
        
        <!-- Dashboard content -->
        <main class="p-4 lg:p-8">
            <div class="mb-8">
                <h2 class="text-2xl font-bold text-gray-900">Dashboard</h2>
                <p class="text-gray-600">Visão geral do sistema</p>
            </div>
            
            <!-- Stats cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-600">Total Usuários</p>
                            <p class="text-2xl font-bold text-gray-900">1,234</p>
                        </div>
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                            </svg>
                        </div>
                    </div>
                </div>
                
                <!-- Mais cards... -->
            </div>
        </main>
    </div>
</div>
{% endblock %}
```

---

## FASE 6: Painel do Usuário

### 6.1 Estrutura do User Panel
```python
# user_panel/views.py
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'user_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adicionar contas do usuário
        context['user_accounts'] = self.request.user.accountmembership_set.filter(is_active=True)
        return context
```

### 6.2 Template Mobile-First para Usuários
```html
<!-- user_panel/templates/user_panel/dashboard.html -->
{% extends 'user_panel/base.html' %}

{% block content %}
<div class="min-h-screen bg-gray-50">
    <!-- Mobile header -->
    <header class="bg-white shadow-sm border-b border-gray-200 lg:hidden">
        <div class="flex items-center justify-between px-4 py-4">
            <h1 class="text-lg font-semibold text-gray-900">Dashboard</h1>
            <button id="mobile-menu-toggle" class="p-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
            </button>
        </div>
    </header>
    
    <!-- Mobile navigation -->
    <nav class="fixed inset-0 z-50 bg-black bg-opacity-50 hidden" id="mobile-menu">
        <div class="fixed right-0 top-0 h-full w-64 bg-white shadow-lg transform translate-x-full transition-transform duration-200 ease-in-out" id="mobile-nav">
            <!-- Navigation content -->
        </div>
    </nav>
    
    <!-- Desktop sidebar -->
    <div class="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-50 lg:block lg:w-64 lg:bg-white lg:shadow-lg">
        <!-- Sidebar content -->
    </div>
    
    <!-- Main content -->
    <div class="lg:ml-64">
        <main class="p-4 lg:p-8">
            <!-- Welcome section -->
            <div class="mb-6">
                <h2 class="text-xl lg:text-2xl font-bold text-gray-900">Olá, {{ user.first_name|default:user.username }}!</h2>
                <p class="text-sm lg:text-base text-gray-600">Bem-vindo ao seu painel</p>
            </div>
            
            <!-- Quick actions - Mobile optimized -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <a href="#" class="bg-white rounded-lg shadow p-4 text-center hover:shadow-md transition-shadow">
                    <div class="w-8 h-8 lg:w-12 lg:h-12 bg-blue-100 rounded-lg mx-auto mb-2 flex items-center justify-center">
                        <svg class="w-4 h-4 lg:w-6 lg:h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                    </div>
                    <p class="text-xs lg:text-sm font-medium text-gray-900">Novo Conteúdo</p>
                </a>
                
                <!-- Mais ações... -->
            </div>
            
            <!-- Accounts list -->
            <div class="bg-white rounded-lg shadow">
                <div class="px-4 py-5 lg:px-6">
                    <h3 class="text-lg font-medium text-gray-900">Suas Contas</h3>
                    <p class="text-sm text-gray-600">Contas que você tem acesso</p>
                </div>
                
                <div class="border-t border-gray-200">
                    {% for membership in user_accounts %}
                    <div class="px-4 py-4 lg:px-6 border-b border-gray-200 last:border-b-0">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <h4 class="text-sm lg:text-base font-medium text-gray-900">{{ membership.account.name }}</h4>
                                <p class="text-xs lg:text-sm text-gray-600">{{ membership.get_role_display }}</p>
                            </div>
                            <a href="#" class="text-sm text-primary-600 hover:text-primary-800">Acessar</a>
                        </div>
                    </div>
                    {% empty %}
                    <div class="px-4 py-8 lg:px-6 text-center">
                        <p class="text-gray-500">Você ainda não faz parte de nenhuma conta</p>
                        <a href="#" class="mt-2 inline-block text-sm text-primary-600 hover:text-primary-800">Criar nova conta</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </main>
    </div>
</div>
{% endblock %}
```

---

## FASE 7: API REST

### 7.1 Serializers
```python
# api/serializers.py
from rest_framework import serializers
from users.models import User
from accounts.models import Account, AccountMembership

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'slug', 'email', 'phone', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class AccountMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account = AccountSerializer(read_only=True)
    
    class Meta:
        model = AccountMembership
        fields = ['id', 'user', 'account', 'role', 'is_active', 'joined_at']
```

### 7.2 ViewSets da API
```python
# api/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, AccountSerializer
from users.models import User
from accounts.models import Account

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar apenas contas que o usuário tem acesso
        return Account.objects.filter(
            accountmembership__user=self.request.user,
            accountmembership__is_active=True
        )
```

---

## FASE 8: Sistema de Pagamentos

### 8.1 Modelos de Pagamento
```python
# payments/models.py
from django.db import models
from django.conf import settings

class Plan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, default='monthly')  # monthly, yearly
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('canceled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('pending', 'Pendente'),
    ]
    
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('canceled', 'Cancelado'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50)  # credit_card, pix, boleto
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
```

---

## FASE 9: Testes e Deploy

### 9.1 Configuração de Testes
```python
# tests/test_users.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Account, AccountMembership

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.status, 'active')
    
    def test_user_can_join_account(self):
        account = Account.objects.create(
            name='Test Company',
            slug='test-company',
            email='company@example.com'
        )
        
        membership = AccountMembership.objects.create(
            user=self.user,
            account=account,
            role='member'
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.account, account)
```

### 9.2 Configuração para Produção
```python
# settings/production.py
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## FASE 10: Checklist Final

### ✅ Funcionalidades Implementadas
- [ ] Sistema de usuários com perfis customizados
- [ ] Multi-tenancy com contas e memberships
- [ ] Sistema RBAC de permissões
- [ ] API REST completa
- [ ] Painel administrativo responsivo
- [ ] Painel do usuário mobile-first
- [ ] Sistema de pagamentos
- [ ] Autenticação JWT
- [ ] Testes automatizados
- [ ] Configuração de produção

### 🎨 Design e UX
- [ ] Layout responsivo com Tailwind CSS
- [ ] Design mobile-first
- [ ] Interface clean e intuitiva
- [ ] Componentes reutilizáveis
- [ ] Navegação otimizada para mobile

### 🔧 Configurações Técnicas
- [ ] Configuração do ambiente de desenvolvimento
- [ ] Configuração do Tailwind CSS
- [ ] Configuração do Django REST Framework
- [ ] Configuração de autenticação JWT
- [ ] Configuração de testes
- [ ] Configuração para produção

---

## Próximos Passos

1. **Implementar autenticação social** (Google, GitHub)
2. **Adicionar notificações em tempo real** (WebSockets)
3. **Implementar cache** (Redis)
4. **Adicionar monitoramento** (Sentry)
5. **Implementar CI/CD** (GitHub Actions)
6. **Adicionar documentação da API** (Swagger)
7. **Implementar testes E2E** (Playwright)
8. **Otimizar performance** (Database indexing, query optimization)

---

## Dúvidas e Questões

**Perguntas para o cliente:**

1. **Gateway de Pagamento**: Qual gateway prefere? (Stripe, MercadoPago, Pagar.me)
2. **Autenticação Social**: Deseja login com Google/GitHub?
3. **Notificações**: Prefere email, SMS ou push notifications?
4. **Domínios**: Como funcionará a validação de domínios?
5. **Limites**: Haverá limites de uso por plano?
6. **Backup**: Qual estratégia de backup prefere?
7. **Monitoramento**: Deseja dashboards de analytics?
8. **Integrações**: Haverá integrações com outros sistemas?

**Decisões Técnicas Pendentes:**

- Escolha do gateway de pagamento
- Estratégia de cache
- Configuração de email (SMTP)
- Configuração de storage (AWS S3, local)
- Configuração de logs
- Estratégia de backup

---

*Este documento será atualizado conforme o desenvolvimento progride e novas necessidades são identificadas.*