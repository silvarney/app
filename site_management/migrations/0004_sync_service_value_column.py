from django.db import migrations

class Migration(migrations.Migration):
    """Garantir que a coluna 'value' exista na tabela service.

    O estado das migrações já considera o campo (estava em 0001), porém o banco atual
    está sem a coluna. Esta migração apenas sincroniza o schema real sem alterar o estado lógico.
    """

    dependencies = [
        ('site_management', '0003_merge_20250905_1202'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE site_management_service ADD COLUMN IF NOT EXISTS value NUMERIC(10,2);",
            reverse_sql="ALTER TABLE site_management_service DROP COLUMN IF EXISTS value;"
        )
    ]
