"""
Guia para migração de modelos Django de ID para UUID
===================================================

Este arquivo contém o código e instruções necessárias para migrar corretamente seus modelos
Django de ID auto-incrementável para UUID.

PASSOS PARA MIGRAÇÃO:

1. Backup do banco de dados (recomendado)
------------------------------------------
Antes de iniciar, sempre faça backup do seu banco de dados:

PostgreSQL:
```
pg_dump -U seu_usuario -d seu_banco -f backup_antes_migracao.sql
```

2. Remover arquivos de migração existentes
------------------------------------------
Remova todos os arquivos de migração existentes, exceto o arquivo __init__.py:

```python
import os
import shutil

apps = ['accounts', 'admin_panel', 'api', 'content', 'domains', 'payments', 
       'permissions', 'settings', 'site_management', 'tasks', 'users']

for app in apps:
    migration_dir = os.path.join(app, 'migrations')
    
    if os.path.exists(migration_dir):
        # Manter apenas o __init__.py
        for filename in os.listdir(migration_dir):
            if filename != '__init__.py' and filename.endswith('.py'):
                filepath = os.path.join(migration_dir, filename)
                os.remove(filepath)
                print(f"Removido: {filepath}")
            
            # Remover arquivos .pyc em __pycache__ se existir
            pycache_dir = os.path.join(migration_dir, '__pycache__')
            if os.path.exists(pycache_dir):
                shutil.rmtree(pycache_dir)
                print(f"Removido diretório: {pycache_dir}")
```

3. Atualizar os modelos para usar UUID
-------------------------------------
Para cada modelo, modifique o campo ID para usar UUID:

```python
import uuid
from django.db import models

class SeuModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # outros campos...
```

4. Verificar ForeignKeys e relações
----------------------------------
Certifique-se de que todas as ForeignKeys estão apontando para modelos com o mesmo tipo de chave primária.
Se um modelo usa UUID como chave primária, todos os modelos que têm ForeignKey para ele também devem esperar UUID.

5. Criar novas migrações
-----------------------
Depois de modificar todos os modelos:

```
python manage.py makemigrations
```

6. Aplicar migrações
------------------
Como estamos recriando o banco de dados:

```
python manage.py migrate
```

7. Criar superusuário
-------------------
Após a migração, crie um novo superusuário:

```
python manage.py createsuperuser
```

8. Verificar se tudo funciona
---------------------------
Execute os testes para verificar se a aplicação está funcionando corretamente.

NOTAS IMPORTANTES:
- Esta abordagem recria o banco de dados do zero, perdendo todos os dados.
- Se precisar preservar dados, será necessária uma migração mais complexa.
- Todos os modelos referenciados por ForeignKeys devem usar o mesmo tipo de chave primária.
- Certifique-se de atualizar seu código para lidar com UUIDs em vez de IDs numéricos.
"""
