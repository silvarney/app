from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('site_management', '0005_sync_service_discount_column'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteAPIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key_prefix', models.CharField(db_index=True, max_length=16, verbose_name='Prefixo')),
                ('key_hash', models.CharField(max_length=128, unique=True, verbose_name='Hash')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='Nome de Referência')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Último Uso')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='site_management.site', verbose_name='Site')),
            ],
            options={
                'verbose_name': 'Chave de API do Site',
                'verbose_name_plural': 'Chaves de API dos Sites',
                'ordering': ['-created_at'],
            },
        ),
    ]
