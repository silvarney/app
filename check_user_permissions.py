#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from permissions.models import UserRole, UserPermission, Role, Permission
from permissions.decorators import get_user_permissions, get_user_roles
from accounts.models import Account

User = get_user_model()

def check_user_permissions():
    print("=== INVESTIGAÇÃO DO SISTEMA DE PERMISSÕES ===")
    
    # 1. Verificar usuário usuariocomum@saas.com
    print("\n1. USUÁRIO: usuariocomum@saas.com")
    user = User.objects.filter(email='usuariocomum@saas.com').first()
    
    if not user:
        print("   Usuário não encontrado!")
        return
    
    print(f"   Email: {user.email}")
    print(f"   Is superuser: {user.is_superuser}")
    print(f"   Is staff: {user.is_staff}")
    print(f"   Is active: {user.is_active}")
    
    # 2. Verificar funções do usuário
    print("\n2. FUNÇÕES DO USUÁRIO:")
    user_roles = UserRole.objects.filter(user=user, status='active')
    print(f"   Total de funções ativas: {user_roles.count()}")
    
    for user_role in user_roles:
        print(f"   - {user_role.role.name} ({user_role.role.codename})")
        print(f"     Tipo: {user_role.role.role_type}")
        print(f"     Conta: {user_role.account.name if user_role.account else 'Global'}")
        print(f"     Status: {user_role.status}")
    
    # 3. Verificar permissões diretas do usuário
    print("\n3. PERMISSÕES DIRETAS DO USUÁRIO:")
    user_permissions = UserPermission.objects.filter(user=user, is_active=True)
    print(f"   Total de permissões diretas: {user_permissions.count()}")
    
    for user_perm in user_permissions:
        print(f"   - {user_perm.permission.name} ({user_perm.permission.codename})")
        print(f"     Conta: {user_perm.account.name if user_perm.account else 'Global'}")
        print(f"     Tipo: {user_perm.grant_type}")
    
    # 4. Verificar todas as permissões (diretas + por funções)
    print("\n4. TODAS AS PERMISSÕES (DIRETAS + POR FUNÇÕES):")
    all_permissions = get_user_permissions(user)
    print(f"   Total de permissões: {all_permissions.count()}")
    
    for perm in all_permissions[:15]:  # Mostrar apenas as primeiras 15
        print(f"   - {perm.name} ({perm.codename})")
    
    if all_permissions.count() > 15:
        print(f"   ... e mais {all_permissions.count() - 15} permissões")
    
    # 5. Verificar sistema de permissões geral
    print("\n5. SISTEMA DE PERMISSÕES GERAL:")
    total_permissions = Permission.objects.filter(is_active=True).count()
    total_roles = Role.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    
    print(f"   Total de permissões no sistema: {total_permissions}")
    print(f"   Total de funções no sistema: {total_roles}")
    print(f"   Total de usuários ativos: {total_users}")
    
    # 6. Verificar superadmin
    print("\n6. VERIFICAÇÃO DE SUPERADMIN:")
    superusers = User.objects.filter(is_superuser=True)
    print(f"   Total de superusuários: {superusers.count()}")
    
    for su in superusers:
        print(f"   - {su.email} (is_staff: {su.is_staff}, is_active: {su.is_active})")
    
    # 7. Verificar funções de sistema
    print("\n7. FUNÇÕES DE SISTEMA:")
    system_roles = Role.objects.filter(is_system=True, is_active=True)
    print(f"   Total de funções de sistema: {system_roles.count()}")
    
    for role in system_roles:
        print(f"   - {role.name} ({role.codename})")
        print(f"     Tipo: {role.role_type}")
        print(f"     Prioridade: {role.priority}")
        
        # Verificar permissões da função
        role_perms = role.permissions.filter(is_active=True)
        print(f"     Permissões: {role_perms.count()}")
    
    print("\n=== FIM DA INVESTIGAÇÃO ===")

if __name__ == '__main__':
    check_user_permissions()