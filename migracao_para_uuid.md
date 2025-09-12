# Plano de Migração para UUID

Este documento descreve o plano para migrar todas as entidades do sistema que ainda usam IDs numéricos para UUIDs.

## 1. Preparação Inicial

### 1.1 Backup do banco de dados
```bash
python manage.py dumpdata > database_backup.json
```

### 1.2 Entidades a serem migradas
Baseado na análise do código, as seguintes entidades ainda usam IDs numéricos:

- User (users/models.py)
- Site (site_management/models.py)
- SiteBio (site_management/models.py)
- SiteCategory (site_management/models.py)
- SiteAPIKey (site_management/models.py)
- Content (content/models.py)
- Category (content/models.py)
- Tag (content/models.py)

## 2. Modificação dos Modelos

Para cada modelo, adicionaremos o campo UUID como chave primária. Vamos modificar cada arquivo de modelo:

### 2.1 User Model (users/models.py)

```python
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente
```

### 2.2 Site Models (site_management/models.py)

```python
import uuid

class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente

class SiteBio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente

class SiteCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente

class SiteAPIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente
```

### 2.3 Content Models (content/models.py)

```python
import uuid

class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Restante do modelo existente
```

## 3. Reiniciar o Banco de Dados

Como o sistema está em desenvolvimento, vamos reiniciar o banco de dados:

```bash
# Remover as migrações existentes (exceto __init__.py)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# Remover o banco de dados SQLite (se estiver usando SQLite)
rm db.sqlite3

# Para PostgreSQL (se estiver usando)
psql -U postgres
DROP DATABASE app_db;
CREATE DATABASE app_db;
\q
```

## 4. Criar e Aplicar Novas Migrações

```bash
# Gerar novas migrações para todos os apps
python manage.py makemigrations

# Aplicar as migrações
python manage.py migrate
```

## 5. Verificação e Ajuste de Código Relacionado

### 5.1 Ajustar todas as referências nos templates

Devemos verificar e ajustar todos os templates que usam IDs numéricos em URLs:

#### 5.1.1 Templates com referências a Site

**Antes:**
```html
<a href="{% url 'user_panel:site_edit' site.id %}">Editar</a>
```

**Depois:**
```html
<a href="{% url 'user_panel:site_edit' site.id %}">Editar</a>
```

#### 5.1.2 Templates com referências a User

**Antes:**
```html
<a href="{% url 'admin_panel:user_detail' user.id %}">Detalhes</a>
```

**Depois:**
```html
<a href="{% url 'admin_panel:user_detail' user.id %}">Detalhes</a>
```

### 5.2 Ajustar todas as URLs e Views

#### 5.2.1 URLs para Site (site_management/urls.py)

**Antes:**
```python
path('sites/<int:site_id>/edit/', views.site_edit, name='site_edit'),
```

**Depois:**
```python
path('sites/<uuid:site_id>/edit/', views.site_edit, name='site_edit'),
```

#### 5.2.2 URLs para User (admin_panel/urls.py)

**Antes:**
```python
path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
```

**Depois:**
```python
path('users/<uuid:user_id>/edit/', views.user_edit, name='user_edit'),
```

### 5.3 Ajustar Código que Serializa/Deserializa IDs

#### 5.3.1 Serializers da API (api/serializers.py)

Verificar e ajustar todos os serializadores que lidam com IDs.

#### 5.3.2 Formulários (forms.py em vários apps)

Verificar e ajustar todos os formulários que lidam com IDs.

### 5.4 Ajustar Testes

Atualizar todos os testes que lidam com IDs numéricos para trabalhar com UUIDs.

## 6. Criar um Novo Superusuário

```bash
python manage.py createsuperuser
```

## 7. Testes Finais

1. Testar autenticação de usuários
2. Testar todas as operações CRUD para cada modelo
3. Testar relacionamentos entre modelos
4. Testar a API (se existente)

## 8. Entidades Específicas e Arquivos a Serem Verificados

### 8.1 User e Autenticação
- users/models.py
- users/admin.py
- admin_panel/views.py (funções relacionadas a usuário)
- templates/admin_panel/users/

### 8.2 Site
- site_management/models.py
- site_management/views.py
- site_management/forms.py
- templates/user_panel/sites/
- templates/admin_panel/sites/

### 8.3 Content
- content/models.py
- content/views.py
- content/forms.py
- templates relacionados ao conteúdo

### 8.4 Outros Pontos de Integração
- admin_panel/views.py
- user_panel/views.py
- api/serializers.py
- api/views.py

## 9. Lista de Verificação Final

- [ ] Todos os modelos atualizados
- [ ] Todas as URLs atualizadas
- [ ] Todos os templates atualizados
- [ ] Todos os formulários atualizados
- [ ] Todos os serializadores atualizados
- [ ] Banco de dados reiniciado e migrado
- [ ] Superusuário criado
- [ ] Testes completos realizados

## 10. Possíveis Problemas e Soluções

### 10.1 Serializadores JSON
Os UUIDs não são serializáveis para JSON por padrão. Pode ser necessário ajustar a serialização:

```python
# utils.py
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

# Uso
json.dumps(data, cls=UUIDEncoder)
```

### 10.2 Consultas de URL
Para endpoints da API que recebem UUIDs via query string:

```python
# views.py
user_id = request.GET.get('user_id')
try:
    user_uuid = uuid.UUID(user_id)
    user = User.objects.get(id=user_uuid)
except (ValueError, User.DoesNotExist):
    return Response({"error": "Invalid user ID"}, status=400)
```

## Conclusão

Esta migração melhorará significativamente a segurança do sistema. Com todos os modelos usando UUIDs como chaves primárias, os recursos não serão facilmente enumeráveis, e as URLs se tornarão mais seguras contra tentativas de acesso não autorizado.

Ao realizar esta migração enquanto o sistema está em desenvolvimento, evitamos problemas complexos de migração de dados que surgiriam em um sistema em produção.
