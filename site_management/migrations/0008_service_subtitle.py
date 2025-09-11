from django.db import migrations, models, connection


def add_subtitle_field(apps, schema_editor):
    # Evita duplicação se a coluna já existir
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='site_management_service' AND column_name='subtitle';")
        if cursor.fetchone():
            return
    schema_editor.add_field(
        apps.get_model('site_management', 'Service'),
        models.CharField(max_length=255, blank=True, null=True, verbose_name='Subtítulo', name='subtitle')
    )


class Migration(migrations.Migration):
    dependencies = [
        ('site_management', '0007_service_link'),
    ]

    operations = [
        migrations.RunPython(add_subtitle_field, migrations.RunPython.noop),
    ]
