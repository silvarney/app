#!/usr/bin/env python
"""
Script para criar o Site com ID=1 no banco de dados de produção.
Este script resolve o erro DoesNotExist que ocorre no login do allauth.

Para executar no servidor:
python manage.py shell < create_site.py

Ou execute diretamente:
python create_site.py
"""

import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_project.settings')
django.setup()

from django.contrib.sites.models import Site

def create_or_update_site():
    """
    Cria ou atualiza o Site com ID=1 necessário para o allauth funcionar.
    """
    try:
        # Tentar obter o site existente
        site = Site.objects.get(pk=1)
        print(f"Site com ID=1 já existe: {site.domain} - {site.name}")
        
        # Atualizar com os valores corretos se necessário
        if site.domain != 'app.criaremos.com' or site.name != 'App Criaremos':
            site.domain = 'app.criaremos.com'
            site.name = 'App Criaremos'
            site.save()
            print("Site atualizado com sucesso!")
        else:
            print("Site já está configurado corretamente.")
            
    except Site.DoesNotExist:
        # Criar o site se não existir
        site = Site.objects.create(
            pk=1,
            domain='app.criaremos.com',
            name='App Criaremos'
        )
        print(f"Site criado com sucesso: {site.domain} - {site.name}")
        
    except Exception as e:
        print(f"Erro ao criar/atualizar o site: {e}")
        return False
        
    return True

def verify_site():
    """
    Verifica se o site foi criado corretamente.
    """
    try:
        site = Site.objects.get(pk=1)
        print(f"\nVerificação:")
        print(f"ID: {site.pk}")
        print(f"Domain: {site.domain}")
        print(f"Name: {site.name}")
        return True
    except Site.DoesNotExist:
        print("ERRO: Site com ID=1 não foi encontrado!")
        return False

if __name__ == '__main__':
    print("=== Criando/Atualizando Site para Produção ===")
    
    if create_or_update_site():
        verify_site()
        print("\n✅ Site configurado com sucesso! O login deve funcionar agora.")
    else:
        print("\n❌ Falha ao configurar o site.")
        sys.exit(1)