from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('site_management', '0009_adjust_service_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitecategory',
            name='is_blog',
            field=models.BooleanField(default=False, verbose_name='Categoria de Blog'),
        ),
    ]
