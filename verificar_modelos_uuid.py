"""
Script para verificar se todos os modelos estão usando UUID como chave primária
"""
import os
import importlib
import inspect
from django.db import models
from django.apps import apps
from django.db.models.fields import UUIDField

def verificar_modelos_uuid():
    """
    Verifica todos os modelos do projeto e lista aqueles que não estão usando UUID como chave primária
    """
    print("Verificando modelos sem UUID como chave primária...")
    
    modelos_nao_uuid = []
    
    # Itera sobre todos os modelos registrados no Django
    for model in apps.get_models():
        # Verifica se o campo ID é um UUIDField
        pk_field = model._meta.pk
        if not isinstance(pk_field, UUIDField):
            modelos_nao_uuid.append(model.__name__)
            print(f"ATENÇÃO: O modelo {model.__name__} em {model.__module__} não usa UUID como chave primária!")
            print(f"  - Tipo atual: {type(pk_field).__name__}")
    
    if not modelos_nao_uuid:
        print("Todos os modelos estão utilizando UUID como chave primária!")
    else:
        print(f"\nTotal de modelos que precisam ser convertidos: {len(modelos_nao_uuid)}")
        print("Modelos:", ", ".join(modelos_nao_uuid))

if __name__ == "__main__":
    print("Este script precisa ser executado com 'python manage.py shell' e então importado:")
    print(">>> from verificar_modelos_uuid import verificar_modelos_uuid")
    print(">>> verificar_modelos_uuid()")
