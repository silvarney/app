from django.core.management.base import BaseCommand
from permissions.models import Permission, Role, RolePermission
from django.contrib.contenttypes.models import ContentType
from settings.models import GlobalSetting, AccountSetting, UserSetting

class Command(BaseCommand):
    help = 'Popula permissões específicas para o sistema de configurações'

    def handle(self, *args, **options):
        self.stdout.write('Criando permissões para o sistema de configurações...')
        
        # Obter content types dos modelos de configuração
        global_setting_ct = ContentType.objects.get_for_model(GlobalSetting)
        account_setting_ct = ContentType.objects.get_for_model(AccountSetting)
        user_setting_ct = ContentType.objects.get_for_model(UserSetting)
        
        # Permissões para configurações globais
        global_permissions = [
            {
                'name': 'Visualizar Configurações Globais',
                'codename': 'view_global_settings',
                'description': 'Permite visualizar configurações globais do sistema',
                'permission_type': 'read',
                'resource': 'global_settings',
                'category': 'settings',
                'content_type': global_setting_ct
            },
            {
                'name': 'Editar Configurações Globais',
                'codename': 'change_global_settings',
                'description': 'Permite editar configurações globais do sistema',
                'permission_type': 'update',
                'resource': 'global_settings',
                'category': 'settings',
                'content_type': global_setting_ct
            },
            {
                'name': 'Gerenciar Configurações Globais',
                'codename': 'manage_global_settings',
                'description': 'Permite gerenciar completamente as configurações globais',
                'permission_type': 'manage',
                'resource': 'global_settings',
                'category': 'settings',
                'content_type': global_setting_ct
            }
        ]
        
        # Permissões para configurações de conta
        account_permissions = [
            {
                'name': 'Visualizar Configurações da Conta',
                'codename': 'view_account_settings',
                'description': 'Permite visualizar configurações da própria conta',
                'permission_type': 'read',
                'resource': 'account_settings',
                'category': 'settings',
                'content_type': account_setting_ct
            },
            {
                'name': 'Editar Configurações da Conta',
                'codename': 'change_account_settings',
                'description': 'Permite editar configurações da própria conta',
                'permission_type': 'update',
                'resource': 'account_settings',
                'category': 'settings',
                'content_type': account_setting_ct
            },
            {
                'name': 'Gerenciar Configurações da Conta',
                'codename': 'manage_account_settings',
                'description': 'Permite gerenciar completamente as configurações da conta',
                'permission_type': 'manage',
                'resource': 'account_settings',
                'category': 'settings',
                'content_type': account_setting_ct
            }
        ]
        
        # Permissões para configurações de usuário
        user_permissions = [
            {
                'name': 'Visualizar Configurações Pessoais',
                'codename': 'view_user_settings',
                'description': 'Permite visualizar as próprias configurações',
                'permission_type': 'read',
                'resource': 'user_settings',
                'category': 'settings',
                'content_type': user_setting_ct
            },
            {
                'name': 'Editar Configurações Pessoais',
                'codename': 'change_user_settings',
                'description': 'Permite editar as próprias configurações',
                'permission_type': 'update',
                'resource': 'user_settings',
                'category': 'settings',
                'content_type': user_setting_ct
            }
        ]
        
        # Criar todas as permissões
        all_permissions = global_permissions + account_permissions + user_permissions
        
        for perm_data in all_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            if created:
                self.stdout.write(f'  ✓ Permissão criada: {permission.name}')
            else:
                self.stdout.write(f'  - Permissão já existe: {permission.name}')
        
        # Criar funções específicas para configurações
        self.stdout.write('\nCriando funções para configurações...')
        
        # Função de Administrador de Sistema
        system_admin_role, created = Role.objects.get_or_create(
            codename='system_admin',
            defaults={
                'name': 'Administrador do Sistema',
                'description': 'Acesso completo a todas as configurações do sistema',
                'role_type': 'system',
                'is_system': True,
                'priority': 100
            }
        )
        
        if created:
            self.stdout.write('  ✓ Função criada: Administrador do Sistema')
            # Adicionar todas as permissões de configuração
            for perm_data in all_permissions:
                permission = Permission.objects.get(codename=perm_data['codename'])
                RolePermission.objects.get_or_create(
                    role=system_admin_role,
                    permission=permission
                )
        else:
            self.stdout.write('  - Função já existe: Administrador do Sistema')
        
        # Função de Gerente de Conta
        account_manager_role, created = Role.objects.get_or_create(
            codename='account_manager',
            defaults={
                'name': 'Gerente da Conta',
                'description': 'Gerencia configurações da conta e usuários',
                'role_type': 'account',
                'priority': 80
            }
        )
        
        if created:
            self.stdout.write('  ✓ Função criada: Gerente da Conta')
            # Adicionar permissões de conta e usuário
            account_user_perms = account_permissions + user_permissions
            for perm_data in account_user_perms:
                permission = Permission.objects.get(codename=perm_data['codename'])
                RolePermission.objects.get_or_create(
                    role=account_manager_role,
                    permission=permission
                )
        else:
            self.stdout.write('  - Função já existe: Gerente da Conta')
        
        # Função de Usuário Padrão
        standard_user_role, created = Role.objects.get_or_create(
            codename='standard_user',
            defaults={
                'name': 'Usuário Padrão',
                'description': 'Acesso básico às próprias configurações',
                'role_type': 'system',
                'is_system': True,
                'priority': 10
            }
        )
        
        if created:
            self.stdout.write('  ✓ Função criada: Usuário Padrão')
            # Adicionar apenas permissões de usuário
            for perm_data in user_permissions:
                permission = Permission.objects.get(codename=perm_data['codename'])
                RolePermission.objects.get_or_create(
                    role=standard_user_role,
                    permission=permission
                )
        else:
            self.stdout.write('  - Função já existe: Usuário Padrão')
        
        self.stdout.write('\n' + self.style.SUCCESS('Permissões de configurações criadas com sucesso!'))
        self.stdout.write(f'Total de permissões de configurações: {Permission.objects.filter(category="settings").count()}')
        self.stdout.write(f'Total de funções: {Role.objects.count()}')