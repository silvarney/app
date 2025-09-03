from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Permission, Role, RolePermission


@receiver(post_migrate)
def create_default_permissions(sender, **kwargs):
    """Cria permissões padrão após as migrações."""
    if sender.name != 'permissions':
        return
    
    # Permissões básicas do sistema
    default_permissions = [
        # Usuários
        {'name': 'Visualizar Usuários', 'codename': 'view_users', 'permission_type': 'read', 'resource': 'user', 'category': 'user_management'},
        {'name': 'Criar Usuários', 'codename': 'create_users', 'permission_type': 'create', 'resource': 'user', 'category': 'user_management'},
        {'name': 'Editar Usuários', 'codename': 'edit_users', 'permission_type': 'update', 'resource': 'user', 'category': 'user_management'},
        {'name': 'Excluir Usuários', 'codename': 'delete_users', 'permission_type': 'delete', 'resource': 'user', 'category': 'user_management'},
        
        # Contas
        {'name': 'Visualizar Contas', 'codename': 'view_accounts', 'permission_type': 'read', 'resource': 'account', 'category': 'account_management'},
        {'name': 'Criar Contas', 'codename': 'create_accounts', 'permission_type': 'create', 'resource': 'account', 'category': 'account_management'},
        {'name': 'Editar Contas', 'codename': 'edit_accounts', 'permission_type': 'update', 'resource': 'account', 'category': 'account_management'},
        {'name': 'Excluir Contas', 'codename': 'delete_accounts', 'permission_type': 'delete', 'resource': 'account', 'category': 'account_management'},
        
        # Membros da Conta
        {'name': 'Visualizar Membros', 'codename': 'view_members', 'permission_type': 'read', 'resource': 'member', 'category': 'member_management'},
        {'name': 'Convidar Membros', 'codename': 'invite_members', 'permission_type': 'create', 'resource': 'member', 'category': 'member_management'},
        {'name': 'Editar Membros', 'codename': 'edit_members', 'permission_type': 'update', 'resource': 'member', 'category': 'member_management'},
        {'name': 'Remover Membros', 'codename': 'remove_members', 'permission_type': 'delete', 'resource': 'member', 'category': 'member_management'},
        
        # Funções e Permissões
        {'name': 'Visualizar Funções', 'codename': 'view_roles', 'permission_type': 'read', 'resource': 'role', 'category': 'permission_management'},
        {'name': 'Criar Funções', 'codename': 'create_roles', 'permission_type': 'create', 'resource': 'role', 'category': 'permission_management'},
        {'name': 'Editar Funções', 'codename': 'edit_roles', 'permission_type': 'update', 'resource': 'role', 'category': 'permission_management'},
        {'name': 'Excluir Funções', 'codename': 'delete_roles', 'permission_type': 'delete', 'resource': 'role', 'category': 'permission_management'},
        
        {'name': 'Visualizar Permissões', 'codename': 'view_permissions', 'permission_type': 'read', 'resource': 'permission', 'category': 'permission_management'},
        {'name': 'Gerenciar Permissões', 'codename': 'manage_permissions', 'permission_type': 'manage', 'resource': 'permission', 'category': 'permission_management'},
        
        # Dashboard e Relatórios
        {'name': 'Visualizar Dashboard', 'codename': 'view_dashboard', 'permission_type': 'read', 'resource': 'dashboard', 'category': 'dashboard'},
        {'name': 'Visualizar Relatórios', 'codename': 'view_reports', 'permission_type': 'read', 'resource': 'report', 'category': 'reporting'},
        {'name': 'Exportar Relatórios', 'codename': 'export_reports', 'permission_type': 'export', 'resource': 'report', 'category': 'reporting'},
        
        # Configurações
        {'name': 'Visualizar Configurações', 'codename': 'view_settings', 'permission_type': 'read', 'resource': 'settings', 'category': 'settings'},
        {'name': 'Editar Configurações', 'codename': 'edit_settings', 'permission_type': 'update', 'resource': 'settings', 'category': 'settings'},
        
        # Billing e Pagamentos
        {'name': 'Visualizar Faturamento', 'codename': 'view_billing', 'permission_type': 'read', 'resource': 'billing', 'category': 'billing'},
        {'name': 'Gerenciar Faturamento', 'codename': 'manage_billing', 'permission_type': 'manage', 'resource': 'billing', 'category': 'billing'},
    ]
    
    for perm_data in default_permissions:
        Permission.objects.get_or_create(
            codename=perm_data['codename'],
            defaults=perm_data
        )
    
    print(f"Criadas {len(default_permissions)} permissões padrão.")


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """Cria funções padrão após as migrações."""
    if sender.name != 'permissions':
        return
    
    # Funções padrão do sistema
    default_roles = [
        {
            'name': 'Super Administrador',
            'codename': 'super_admin',
            'description': 'Acesso total ao sistema',
            'role_type': 'system',
            'priority': 1000,
            'is_system': True,
            'permissions': 'all'  # Todas as permissões
        },
        {
            'name': 'Administrador',
            'codename': 'admin',
            'description': 'Administrador da conta com acesso completo',
            'role_type': 'account',
            'priority': 900,
            'is_system': True,
            'permissions': [
                'view_users', 'create_users', 'edit_users', 'delete_users',
                'view_accounts', 'edit_accounts',
                'view_members', 'invite_members', 'edit_members', 'remove_members',
                'view_roles', 'create_roles', 'edit_roles', 'delete_roles',
                'view_permissions', 'manage_permissions',
                'view_dashboard', 'view_reports', 'export_reports',
                'view_settings', 'edit_settings',
                'view_billing', 'manage_billing'
            ]
        },
        {
            'name': 'Gerente',
            'codename': 'manager',
            'description': 'Gerente com permissões de gestão limitadas',
            'role_type': 'account',
            'priority': 700,
            'is_system': True,
            'permissions': [
                'view_users', 'create_users', 'edit_users',
                'view_accounts',
                'view_members', 'invite_members', 'edit_members',
                'view_roles', 'view_permissions',
                'view_dashboard', 'view_reports',
                'view_settings'
            ]
        },
        {
            'name': 'Editor',
            'codename': 'editor',
            'description': 'Editor com permissões de edição',
            'role_type': 'account',
            'priority': 500,
            'is_system': True,
            'permissions': [
                'view_users', 'edit_users',
                'view_accounts',
                'view_members',
                'view_dashboard', 'view_reports',
                'view_settings'
            ]
        },
        {
            'name': 'Visualizador',
            'codename': 'viewer',
            'description': 'Usuário com permissões apenas de visualização',
            'role_type': 'account',
            'priority': 300,
            'is_system': True,
            'permissions': [
                'view_users',
                'view_accounts',
                'view_members',
                'view_dashboard',
                'view_settings'
            ]
        },
        {
            'name': 'Membro',
            'codename': 'member',
            'description': 'Membro básico da conta',
            'role_type': 'account',
            'priority': 100,
            'is_system': True,
            'permissions': [
                'view_dashboard'
            ]
        }
    ]
    
    for role_data in default_roles:
        permissions_list = role_data.pop('permissions')
        role, created = Role.objects.get_or_create(
            codename=role_data['codename'],
            defaults=role_data
        )
        
        if created or not role.rolepermission_set.exists():
            # Adicionar permissões à função
            if permissions_list == 'all':
                # Super admin tem todas as permissões
                all_permissions = Permission.objects.filter(is_active=True)
                for permission in all_permissions:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission,
                        defaults={'is_active': True}
                    )
            else:
                # Adicionar permissões específicas
                for perm_codename in permissions_list:
                    try:
                        permission = Permission.objects.get(codename=perm_codename)
                        RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission,
                            defaults={'is_active': True}
                        )
                    except Permission.DoesNotExist:
                        print(f"Permissão '{perm_codename}' não encontrada para a função '{role.name}'")
    
    print(f"Criadas {len(default_roles)} funções padrão.")