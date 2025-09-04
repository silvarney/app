import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from accounts.models import Account
from settings.models import GlobalSetting, AccountSetting, UserSetting, SettingTemplate
import json

User = get_user_model()


class GlobalSettingModelTest(TestCase):
    """Testes para o modelo GlobalSetting"""
    
    def setUp(self):
        self.global_setting = GlobalSetting.objects.create(
            key='test_setting',
            value='test_value',
            setting_type='string',
            description='Test setting description',
            category='test'
        )
    
    def test_string_representation(self):
        """Testa a representação string do modelo"""
        expected = f"test_setting: test_value"
        self.assertEqual(str(self.global_setting), expected)
    
    def test_get_typed_value_string(self):
        """Testa conversão de valor para string"""
        self.assertEqual(self.global_setting.get_typed_value(), 'test_value')
    
    def test_get_typed_value_integer(self):
        """Testa conversão de valor para integer"""
        setting = GlobalSetting.objects.create(
            key='int_setting',
            value='42',
            setting_type='integer'
        )
        self.assertEqual(setting.get_typed_value(), 42)
        self.assertIsInstance(setting.get_typed_value(), int)
    
    def test_get_typed_value_float(self):
        """Testa conversão de valor para float"""
        setting = GlobalSetting.objects.create(
            key='float_setting',
            value='3.14',
            setting_type='float'
        )
        self.assertEqual(setting.get_typed_value(), 3.14)
        self.assertIsInstance(setting.get_typed_value(), float)
    
    def test_get_typed_value_boolean_true(self):
        """Testa conversão de valor para boolean (true)"""
        setting = GlobalSetting.objects.create(
            key='bool_setting',
            value='true',
            setting_type='boolean'
        )
        self.assertTrue(setting.get_typed_value())
    
    def test_get_typed_value_boolean_false(self):
        """Testa conversão de valor para boolean (false)"""
        setting = GlobalSetting.objects.create(
            key='bool_setting_false',
            value='false',
            setting_type='boolean'
        )
        self.assertFalse(setting.get_typed_value())
    
    def test_get_typed_value_json(self):
        """Testa conversão de valor para JSON"""
        test_data = {'key': 'value', 'number': 42}
        setting = GlobalSetting.objects.create(
            key='json_setting',
            value=json.dumps(test_data),
            setting_type='json'
        )
        self.assertEqual(setting.get_typed_value(), test_data)
    
    def test_set_typed_value_json(self):
        """Testa definição de valor JSON"""
        test_data = {'test': 'data'}
        setting = GlobalSetting.objects.create(
            key='json_set_test',
            value='',
            setting_type='json'
        )
        setting.set_typed_value(test_data)
        self.assertEqual(setting.value, json.dumps(test_data))
    
    def test_set_typed_value_string(self):
        """Testa definição de valor string"""
        setting = GlobalSetting.objects.create(
            key='string_set_test',
            value='',
            setting_type='string'
        )
        setting.set_typed_value('new_value')
        self.assertEqual(setting.value, 'new_value')
    
    def test_unique_key_constraint(self):
        """Testa que a chave deve ser única"""
        with self.assertRaises(Exception):
            GlobalSetting.objects.create(
                key='test_setting',  # Chave já existe
                value='another_value'
            )


class AccountSettingModelTest(TestCase):
    """Testes para o modelo AccountSetting"""
    
    def setUp(self):
        # Criar usuário proprietário
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        
        # Criar conta
        self.account = Account.objects.create(
            name='Test Account',
            slug='test-account',
            owner=self.owner
        )
        self.account_setting = AccountSetting.objects.create(
            account=self.account,
            key='account_test_setting',
            value='account_test_value',
            setting_type='string',
            description='Account test setting'
        )
    
    def test_string_representation(self):
        """Testa a representação string do modelo"""
        expected = f"Test Account - account_test_setting: account_test_value"
        self.assertEqual(str(self.account_setting), expected)
    
    def test_account_relationship(self):
        """Testa o relacionamento com Account"""
        self.assertEqual(self.account_setting.account, self.account)
        self.assertIn(self.account_setting, self.account.settings.all())
    
    def test_unique_together_constraint(self):
        """Testa que account + key devem ser únicos"""
        with self.assertRaises(Exception):
            AccountSetting.objects.create(
                account=self.account,
                key='account_test_setting',  # Chave já existe para esta conta
                value='another_value'
            )
    
    def test_different_accounts_same_key(self):
        """Testa que contas diferentes podem ter a mesma chave"""
        another_owner = User.objects.create_user(
            username='another_owner',
            email='another_owner@example.com',
            password='ownerpass123'
        )
        another_account = Account.objects.create(
            name='Another Account',
            slug='another-account',
            owner=another_owner
        )
        # Deve funcionar sem erro
        AccountSetting.objects.create(
            account=another_account,
            key='account_test_setting',  # Mesma chave, conta diferente
            value='another_value'
        )


class UserSettingModelTest(TestCase):
    """Testes para o modelo UserSetting"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Criar conta
        self.account = Account.objects.create(
            name='Test Account',
            slug='test-account',
            owner=self.user
        )
        self.user_setting = UserSetting.objects.create(
            user=self.user,
            key='user_test_setting',
            value='user_test_value',
            setting_type='string',
            description='User test setting'
        )
    
    def test_string_representation(self):
        """Testa a representação string do modelo"""
        expected = f"{self.user.email} - user_test_setting: user_test_value"
        self.assertEqual(str(self.user_setting), expected)
    
    def test_user_relationship(self):
        """Testa o relacionamento com User"""
        self.assertEqual(self.user_setting.user, self.user)
        self.assertIn(self.user_setting, self.user.settings.all())
    
    def test_unique_together_constraint(self):
        """Testa que user + key devem ser únicos"""
        with self.assertRaises(Exception):
            UserSetting.objects.create(
                user=self.user,
                key='user_test_setting',  # Chave já existe para este usuário
                value='another_value'
            )
    
    def test_different_users_same_key(self):
        """Testa que usuários diferentes podem ter a mesma chave"""
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='testpass123'
        )
        # Deve funcionar sem erro
        UserSetting.objects.create(
            user=another_user,
            key='user_test_setting',  # Mesma chave, usuário diferente
            value='another_value'
        )


class SettingTemplateModelTest(TestCase):
    """Testes para o modelo SettingTemplate"""
    
    def setUp(self):
        self.template = SettingTemplate.objects.create(
            key='template_setting',
            name='Template Setting',
            description='A template setting for testing',
            setting_type='string',
            default_value='default',
            category='test',
            scope='global'
        )
    
    def test_string_representation(self):
        """Testa a representação string do modelo"""
        expected = "Template Setting (global)"
        self.assertEqual(str(self.template), expected)
    
    def test_unique_key_constraint(self):
        """Testa que a chave deve ser única"""
        with self.assertRaises(Exception):
            SettingTemplate.objects.create(
                key='template_setting',  # Chave já existe
                name='Another Template',
                description='Another description',
                category='test',
                scope='account'
            )
    
    def test_validation_rules_json_field(self):
        """Testa o campo JSON de regras de validação"""
        validation_rules = {
            'min_length': 5,
            'max_length': 100,
            'pattern': '^[a-zA-Z0-9]+$'
        }
        template = SettingTemplate.objects.create(
            key='validated_setting',
            name='Validated Setting',
            description='A setting with validation rules',
            category='test',
            scope='user',
            validation_rules=validation_rules
        )
        self.assertEqual(template.validation_rules, validation_rules)
    
    def test_scope_choices(self):
        """Testa os valores válidos para scope"""
        valid_scopes = ['global', 'account', 'user']
        for scope in valid_scopes:
            template = SettingTemplate.objects.create(
                key=f'scope_test_{scope}',
                name=f'Scope Test {scope}',
                description=f'Test for {scope} scope',
                category='test',
                scope=scope
            )
            self.assertEqual(template.scope, scope)
    
    def test_setting_type_choices(self):
        """Testa os valores válidos para setting_type"""
        valid_types = ['string', 'integer', 'float', 'boolean', 'json', 'text']
        for setting_type in valid_types:
            template = SettingTemplate.objects.create(
                key=f'type_test_{setting_type}',
                name=f'Type Test {setting_type}',
                description=f'Test for {setting_type} type',
                category='test',
                scope='global',
                setting_type=setting_type
            )
            self.assertEqual(template.setting_type, setting_type)