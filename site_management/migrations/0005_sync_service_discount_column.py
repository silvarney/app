from django.db import migrations

class Migration(migrations.Migration):
    """Garante a existência da coluna 'discount' em service.

    Cenário: Banco perdeu a coluna apesar de estar no estado lógico inicial.
    Ação: Recria com default 0 se ausente (idempotente via IF NOT EXISTS).
    """

    dependencies = [
        ('site_management', '0004_sync_service_value_column'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE site_management_service ADD COLUMN IF NOT EXISTS discount NUMERIC(5,2) NOT NULL DEFAULT 0;",
            reverse_sql="ALTER TABLE site_management_service DROP COLUMN IF EXISTS discount;"
        )
    ]
