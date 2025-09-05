# Generated manually to ensure Site with ID=1 exists

from django.db import migrations
from django.contrib.sites.models import Site

def create_default_site(apps, schema_editor):
    """
    Cria o Site padrão com ID=1 necessário para o allauth funcionar.
    """
    # Usar o modelo Site através do apps registry para compatibilidade
    Site = apps.get_model('sites', 'Site')
    
    # Verificar se já existe um site com ID=1
    if not Site.objects.filter(pk=1).exists():
        Site.objects.create(
            pk=1,
            domain='app.criaremos.com',
            name='App Criaremos'
        )
        print("Site padrão criado: app.criaremos.com")
    else:
        # Atualizar o site existente se necessário
        site = Site.objects.get(pk=1)
        if site.domain != 'app.criaremos.com' or site.name != 'App Criaremos':
            site.domain = 'app.criaremos.com'
            site.name = 'App Criaremos'
            site.save()
            print("Site padrão atualizado: app.criaremos.com")

def remove_default_site(apps, schema_editor):
    """
    Remove o Site padrão (operação reversa).
    ATENÇÃO: Isso pode quebrar o allauth se executado!
    """
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=1).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('site_management', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),  # Dependência do app sites
    ]

    operations = [
        migrations.RunPython(
            create_default_site,
            remove_default_site,
            hints={'target_db': 'default'}
        ),
    ]