from django.db import migrations

SQL_DROP_OLD_FK = """
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Procura constraint antiga que aponta para content_category
    FOR r IN (
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_name = kcu.table_name
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'site_management_blogpost'
          AND ccu.table_name = 'content_category'
          AND kcu.column_name = 'category_id'
    ) LOOP
        EXECUTE format('ALTER TABLE site_management_blogpost DROP CONSTRAINT %I', r.constraint_name);
    END LOOP;
END $$;
"""

SQL_CREATE_NEW_FK = """
ALTER TABLE site_management_blogpost
    ADD CONSTRAINT site_management_blogpost_category_id_fk
    FOREIGN KEY (category_id) REFERENCES site_management_sitecategory(id) DEFERRABLE INITIALLY DEFERRED;
"""

class Migration(migrations.Migration):
    dependencies = [
        ('site_management', '0012_alter_blogpost_category'),
    ]

    operations = [
        migrations.RunSQL(SQL_DROP_OLD_FK, reverse_sql="""ALTER TABLE site_management_blogpost DROP CONSTRAINT IF EXISTS site_management_blogpost_category_id_fk;"""),
        migrations.RunSQL(SQL_CREATE_NEW_FK, reverse_sql="""-- reverse: not reinstating old constraint"""),
    ]
