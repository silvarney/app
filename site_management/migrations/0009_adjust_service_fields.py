from django.db import migrations, models, connection


def ensure_service_fields(apps, schema_editor):
    with connection.cursor() as cursor:
        # subtitle nullable
        cursor.execute("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name='site_management_service' AND column_name='subtitle';")
        row = cursor.fetchone()
        if row:
            # Make nullable if not
            cursor.execute("ALTER TABLE site_management_service ALTER COLUMN subtitle DROP NOT NULL;")
        else:
            cursor.execute("ALTER TABLE site_management_service ADD COLUMN subtitle varchar(255) NULL;")
        # link column (allow null temporarily, application fills)
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='site_management_service' AND column_name='link';")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE site_management_service ADD COLUMN link varchar(255) NULL;")


class Migration(migrations.Migration):
    dependencies = [
        ('site_management', '0008_service_subtitle'),
    ]

    operations = [
        migrations.RunPython(ensure_service_fields, migrations.RunPython.noop),
    ]
