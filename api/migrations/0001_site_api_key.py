from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = False

    dependencies = [
        ('site_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteAPIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Rótulo interno para identificação da chave', max_length=100)),
                ('key_prefix', models.CharField(db_index=True, max_length=16)),
                ('hashed_key', models.CharField(max_length=128, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='site_management.site')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Site API Key',
                'verbose_name_plural': 'Site API Keys',
            },
        ),
    ]
