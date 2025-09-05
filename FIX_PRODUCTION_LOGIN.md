# Correção do Erro de Login em Produção

## Problema
O erro `DoesNotExist at /login/` ocorre porque o Django allauth precisa de um Site com ID=1 no banco de dados, mas este não existe no servidor de produção.

## Soluções Disponíveis

### Opção 1: Script Direto (Mais Rápido)

Execute no servidor de produção:

```bash
# Copie o arquivo create_site.py para o servidor
# Em seguida, execute:
python create_site.py
```

Ou usando o Django shell:

```bash
python manage.py shell < create_site.py
```

### Opção 2: Migração de Dados (Recomendado para Deploy)

1. **Aplicar a migração no servidor:**
```bash
python manage.py migrate site_management
```

2. **Verificar se funcionou:**
```bash
python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get(pk=1))"
```

### Opção 3: Comando Manual no Django Shell

Se preferir executar manualmente:

```bash
python manage.py shell
```

Dentro do shell:
```python
from django.contrib.sites.models import Site

# Criar o site
site, created = Site.objects.get_or_create(
    pk=1,
    defaults={
        'domain': 'app.criaremos.com',
        'name': 'App Criaremos'
    }
)

print(f"Site {'criado' if created else 'já existia'}: {site.domain}")
exit()
```

## Verificação

Após executar qualquer uma das opções, teste o login em:
- https://app.criaremos.com/login/

O erro `DoesNotExist` deve ter sido resolvido.

## Prevenção Futura

A migração `0002_create_default_site.py` foi criada para garantir que este problema não ocorra novamente em futuros deploys. Sempre execute as migrações após o deploy:

```bash
python manage.py migrate
```

## Configuração do SITE_ID

O arquivo `settings.py` já está configurado corretamente com:
```python
SITE_ID = 1
```

Esta configuração informa ao allauth qual Site usar para autenticação.