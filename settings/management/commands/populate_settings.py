from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Account
from settings.models import GlobalSetting, AccountSetting, UserSetting

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula configurações iniciais do sistema'

    def handle(self, *args, **options):
        self.stdout.write('Criando configurações globais...')
        
        # Configurações globais do sistema
        global_settings = [
            {
                'key': 'site_name',
                'value': 'SaaS Platform',
                'setting_type': 'string',
                'description': 'Nome do site exibido no cabeçalho',
                'category': 'general'
            },
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Ativar modo de manutenção',
                'category': 'system'
            },
            {
                'key': 'max_users_per_account',
                'value': '10',
                'setting_type': 'integer',
                'description': 'Número máximo de usuários por conta',
                'category': 'limits'
            },
            {
                'key': 'default_timezone',
                'value': 'America/Sao_Paulo',
                'setting_type': 'string',
                'description': 'Fuso horário padrão do sistema',
                'category': 'general'
            },
            {
                'key': 'email_notifications',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Habilitar notificações por email',
                'category': 'notifications'
            },
            {
                'key': 'session_timeout',
                'value': '3600',
                'setting_type': 'integer',
                'description': 'Tempo limite da sessão em segundos',
                'category': 'security'
            },
            {
                'key': 'api_rate_limit',
                'value': '1000',
                'setting_type': 'integer',
                'description': 'Limite de requisições por hora na API',
                'category': 'api'
            },
            {
                'key': 'backup_frequency',
                'value': 'daily',
                'setting_type': 'string',
                'description': 'Frequência de backup automático',
                'category': 'system'
            }
        ]
        
        for setting_data in global_settings:
            setting, created = GlobalSetting.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
            if created:
                self.stdout.write(f'  ✓ Configuração global criada: {setting.key}')
            else:
                self.stdout.write(f'  - Configuração global já existe: {setting.key}')
        
        # Configurações padrão para contas
        self.stdout.write('\nCriando configurações padrão para contas...')
        
        account_settings = [
            {
                'key': 'company_name',
                'value': '',
                'setting_type': 'string',
                'description': 'Nome da empresa',
                'category': 'company'
            },
            {
                'key': 'billing_email',
                'value': '',
                'setting_type': 'string',
                'description': 'Email para cobrança',
                'category': 'billing'
            },
            {
                'key': 'auto_invoice',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Gerar faturas automaticamente',
                'category': 'billing'
            },
            {
                'key': 'team_size_limit',
                'value': '5',
                'setting_type': 'integer',
                'description': 'Limite de membros na equipe',
                'category': 'team'
            },
            {
                'key': 'storage_limit_gb',
                'value': '10.0',
                'setting_type': 'float',
                'description': 'Limite de armazenamento em GB',
                'category': 'limits'
            },
            {
                'key': 'notification_frequency',
                'value': 'immediate',
                'setting_type': 'string',
                'description': 'Frequência de notificações',
                'category': 'notifications'
            },
            {
                'key': 'data_retention_days',
                'value': '365',
                'setting_type': 'integer',
                'description': 'Dias de retenção de dados',
                'category': 'data'
            },
            {
                'key': 'api_access_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Habilitar acesso à API',
                'category': 'api'
            }
        ]
        
        # Aplicar configurações para todas as contas existentes
        accounts = Account.objects.all()
        for account in accounts:
            for setting_data in account_settings:
                setting, created = AccountSetting.objects.get_or_create(
                    account=account,
                    key=setting_data['key'],
                    defaults=setting_data
                )
                if created:
                    self.stdout.write(f'  ✓ Configuração criada para conta {account.name}: {setting.key}')
        
        # Configurações padrão para usuários
        self.stdout.write('\nCriando configurações padrão para usuários...')
        
        user_settings = [
            {
                'key': 'language',
                'value': 'pt-br',
                'setting_type': 'string',
                'description': 'Idioma da interface',
                'category': 'personal'
            },
            {
                'key': 'theme',
                'value': 'light',
                'setting_type': 'string',
                'description': 'Tema da interface',
                'category': 'personal'
            },
            {
                'key': 'email_notifications',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Receber notificações por email',
                'category': 'notifications'
            },
            {
                'key': 'dashboard_layout',
                'value': 'grid',
                'setting_type': 'string',
                'description': 'Layout do dashboard',
                'category': 'interface'
            },
            {
                'key': 'items_per_page',
                'value': '25',
                'setting_type': 'integer',
                'description': 'Itens por página nas listagens',
                'category': 'interface'
            },
            {
                'key': 'auto_save',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Salvar automaticamente',
                'category': 'editor'
            },
            {
                'key': 'timezone',
                'value': 'America/Sao_Paulo',
                'setting_type': 'string',
                'description': 'Fuso horário pessoal',
                'category': 'personal'
            },
            {
                'key': 'two_factor_enabled',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Autenticação de dois fatores',
                'category': 'security'
            }
        ]
        
        # Aplicar configurações para todos os usuários existentes
        users = User.objects.all()
        for user in users:
            for setting_data in user_settings:
                setting, created = UserSetting.objects.get_or_create(
                    user=user,
                    key=setting_data['key'],
                    defaults=setting_data
                )
                if created:
                    self.stdout.write(f'  ✓ Configuração criada para usuário {user.username}: {setting.key}')
        
        self.stdout.write('\n' + self.style.SUCCESS('Configurações iniciais criadas com sucesso!'))
        self.stdout.write(f'Total de configurações globais: {GlobalSetting.objects.count()}')
        self.stdout.write(f'Total de configurações de conta: {AccountSetting.objects.count()}')
        self.stdout.write(f'Total de configurações de usuário: {UserSetting.objects.count()}')