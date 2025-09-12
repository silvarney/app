# Instruções para migração de IDs para UUIDs

## Preparação

Antes de iniciar o processo de migração para UUIDs, é importante fazer um backup completo do seu banco de dados e ter um plano de rollback caso algo dê errado.

## Opção 1: Migração completa (ambiente de desenvolvimento)

Esta abordagem é recomendada para ambientes de desenvolvimento onde você pode recriar o banco de dados do zero.

### 1. Backup do banco de dados
```bash
pg_dump -U seu_usuario -d seu_banco -f backup_antes_migracao.sql
```

### 2. Limpar migrações existentes
Execute o script Python para limpar os arquivos de migração:
```bash
python limpar_migracoes.py
```

### 3. Certificar-se que todos os modelos usam UUID
Todos os modelos devem ter sido atualizados para usar UUID como chave primária:
```python
import uuid
from django.db import models

class SeuModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # outros campos...
```

### 4. Criar novas migrações
```bash
python manage.py makemigrations
```

### 5. Recriar o banco de dados
Para PostgreSQL:
```bash
dropdb -U seu_usuario seu_banco
createdb -U seu_usuario seu_banco
```

### 6. Aplicar migrações
```bash
python manage.py migrate
```

### 7. Criar superusuário
```bash
python manage.py createsuperuser
```

## Opção 2: Migração em produção (preservando dados)

Para ambientes de produção, é necessário preservar os dados. Esta é uma abordagem mais complexa e deve ser testada em um ambiente de staging antes.

### 1. Preparação
- Faça backup completo do banco de dados
- Planeje uma janela de manutenção
- Prepare scripts de rollback

### 2. Abordagem recomendada
Para cada modelo:

1. Crie um novo campo UUID temporariamente
   ```python
   uuid_id = models.UUIDField(default=uuid.uuid4, null=True)
   ```

2. Crie e aplique a migração para adicionar o campo
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Preencha o campo UUID para todos os registros existentes
   ```python
   # Em uma migração personalizada:
   for item in ModelName.objects.all():
       item.uuid_id = uuid.uuid4()
       item.save(update_fields=['uuid_id'])
   ```

4. Atualize todas as relações para usar o novo campo
   
5. Remova o campo ID original e renomeie uuid_id para id

6. Faça testes extensivos para garantir que todas as relações foram preservadas

## Recomendações finais

1. **Teste em ambiente de desenvolvimento**: Nunca aplique estas mudanças diretamente em produção
2. **Backup**: Faça backups em todas as etapas do processo
3. **Verificação**: Use o script `verificar_modelos_uuid.py` para garantir que todos os modelos foram convertidos
4. **Testes automatizados**: Execute todos os testes após a migração para validar a funcionalidade

## Solução de problemas comuns

### Conflitos de migração
Se encontrar conflitos de migração:
```bash
python manage.py makemigrations --merge
```

### Erros de integridade de dados
Verifique todas as relações entre modelos para garantir que ForeignKeys estejam usando o tipo correto de campo.

### Compatibilidade com código existente
Atualize todas as partes do código que esperam IDs inteiros para lidar com UUIDs:
- Conversões de string para UUID
- URLs e parâmetros
- Serializers e formulários
