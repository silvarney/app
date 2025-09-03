#!/usr/bin/env python
"""
Script para configurar aplicações sociais no Django Admin
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def setup_social_apps():
    """Configura as aplicações sociais básicas"""
    
    # Obter ou criar o site padrão
    site, created = Site.objects.get_or_create(
        pk=1,
        defaults={
            'domain': 'localhost:8000',
            'name': 'SaaS Local Development'
        }
    )
    
    if created:
        print(f"Site criado: {site.name}")
    else:
        print(f"Site existente: {site.name}")
    
    # Configurar aplicações sociais com credenciais vazias (para desenvolvimento)
    social_apps = [
        {
            'provider': 'google',
            'name': 'Google',
            'client_id': 'your-google-client-id',
            'secret': 'your-google-client-secret'
        },
        {
            'provider': 'facebook',
            'name': 'Facebook',
            'client_id': 'your-facebook-app-id',
            'secret': 'your-facebook-app-secret'
        },
        {
            'provider': 'github',
            'name': 'GitHub',
            'client_id': 'your-github-client-id',
            'secret': 'your-github-client-secret'
        }
    ]
    
    for app_config in social_apps:
        social_app, created = SocialApp.objects.get_or_create(
            provider=app_config['provider'],
            defaults={
                'name': app_config['name'],
                'client_id': app_config['client_id'],
                'secret': app_config['secret']
            }
        )
        
        # Adicionar o site à aplicação social
        social_app.sites.add(site)
        
        if created:
            print(f"Aplicação social criada: {app_config['name']}")
        else:
            print(f"Aplicação social existente: {app_config['name']}")
    
    print("\n✅ Configuração das aplicações sociais concluída!")
    print("\n📝 Nota: As credenciais são placeholders. Para usar login social em produção:")
    print("1. Acesse o Django Admin em http://127.0.0.1:8000/admin/")
    print("2. Vá para 'Social Applications'")
    print("3. Configure as credenciais reais dos provedores")

if __name__ == '__main__':
    setup_social_apps()