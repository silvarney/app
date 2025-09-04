import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from accounts.models import Account
from settings.models import GlobalSetting, AccountSetting, UserSetting, SettingTemplate
from settings.serializers import (
    GlobalSettingSerializer,
    AccountSettingSerializer,
    UserSettingSerializer,
    SettingTemplateSerializer
)

User = get_user_model()


class GlobalSettingSerializerTest(TestCase):
    """Testes para o serializer de configurações globais"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.global_setting = GlobalSetting.objects.create(
            key='test_setting',
            value='test_value',
            setting_type='string',
            description='Test setting',
            category='test'
        )
    
    def test_serialize_global_setting(self):
        """Testa serialização de configuração global"""
        serializer = GlobalSettingSerializer(self.global_setting)
        data = serializer.data
        
        self.assertEqual(data['key'], 'test_setting')
        self.assertEqual(data['value'], 'test_value')
        self.assertEqual(data['setting_type'], 'string')
        self.assertEqual(data['description'], 'Test setting')
        self.assertEqual(data['category'], 'test')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_deserialize_valid_global_setting(self):
        """Testa deserialização válida de configuração global"""
        data = {
            'key': 'new_setting',
            'value': 'new_value',
            'setting_type': 'string',
            'description': 'New setting',
            'category': 'new'
        }
        
        serializer = GlobalSettingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        global_setting = serializer.save()
        self.assertEqual(global_setting.key, 'new_setting')
        self.assertEqual(global_setting.value, 'new_value')
    
    def test_deserialize_invalid_global_setting(self):
        """Testa deserialização inválida de configuração global"""
        data = {
            'key': '',  # Key vazia é inválida
            'value': 'value',
            'setting_type': 'invalid_type'  # Tipo inválido
        }
        
        serializer = GlobalSettingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key', serializer.errors)
        self.assertIn('setting_type', serializer.errors)
    
    def test_unique_key_validation(self):
        """Testa validação de chave única"""
        data = {
            'key': 'test_setting',  # Chave já existe
            'value': 'another_value',
            'setting_type': 'string'
        }
        
        serializer = GlobalSettingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key', serializer.errors)
    
    def test_typed_value_serialization(self):
        """Testa serialização de valores tipados"""
        # Teste com integer
        int_setting = GlobalSetting.objects.create(
            key='int_setting',
            value='42',
            setting_type='integer'
        )
        serializer = GlobalSettingSerializer(int_setting)
        self.assertEqual(serializer.data['typed_value'], 42)
        
        # Teste com boolean
        bool_setting = GlobalSetting.objects.create(
            key='bool_setting',
            value='true',
            setting_type='boolean'
        )
        serializer = GlobalSettingSerializer(bool_setting)
        self.assertEqual(serializer.data['typed_value'], True)
        
        # Teste com float
        float_setting = GlobalSetting.objects.create(
            key='float_setting',
            value='3.14',
            setting_type='float'
        )
        serializer = GlobalSettingSerializer(float_setting)
        self.assertEqual(serializer.data['typed_value'], 3.14)


class AccountSettingSerializerTest(TestCase):
    """Testes para o serializer de configurações de conta"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = Account.objects.create(
            name='Test Account',
            slug='test-account',
            owner=self.user
        )
        self.user.account = self.account
        self.user.save()
        
        self.account_setting = AccountSetting.objects.create(
            account=self.account,
            key='account_test_setting',
            value='account_value',
            setting_type='string',
            description='Account test setting'
        )
    
    def test_serialize_account_setting(self):
        """Testa serialização de configuração de conta"""
        request = APIRequestFactory().get('/')
        request.user = self.user
        
        serializer = AccountSettingSerializer(
            self.account_setting,
            context={'request': request}
        )
        data = serializer.data
        
        self.assertEqual(data['key'], 'account_test_setting')
        self.assertEqual(data['value'], 'account_value')
        self.assertEqual(data['setting_type'], 'string')
        self.assertIn('account', data)
    
    def test_create_account_setting_with_context(self):
        """Testa criação de configuração de conta com contexto"""
        request = APIRequestFactory().post('/')
        request.user = self.user
        
        data = {
            'key': 'new_account_setting',
            'value': 'new_account_value',
            'setting_type': 'string',
            'description': 'New account setting'
        }
        
        serializer = AccountSettingSerializer(
            data=data,
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        
        account_setting = serializer.save(account=self.account)
        self.assertEqual(account_setting.account, self.account)
        self.assertEqual(account_setting.key, 'new_account_setting')
    
    def test_unique_key_per_account_validation(self):
        """Testa validação de chave única por conta"""
        request = APIRequestFactory().post('/')
        request.user = self.user
        
        data = {
            'key': 'account_test_setting',  # Chave já existe para esta conta
            'value': 'another_value',
            'setting_type': 'string'
        }
        
        serializer = AccountSettingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # A validação de unicidade deve ser feita no nível do modelo/banco
        with self.assertRaises(Exception):
            serializer.save(account=self.account)


class UserSettingSerializerTest(TestCase):
    """Testes para o serializer de configurações de usuário"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_setting = UserSetting.objects.create(
            user=self.user,
            key='user_test_setting',
            value='user_value',
            setting_type='string',
            description='User test setting'
        )
    
    def test_serialize_user_setting(self):
        """Testa serialização de configuração de usuário"""
        request = APIRequestFactory().get('/')
        request.user = self.user
        
        serializer = UserSettingSerializer(
            self.user_setting,
            context={'request': request}
        )
        data = serializer.data
        
        self.assertEqual(data['key'], 'user_test_setting')
        self.assertEqual(data['value'], 'user_value')
        self.assertEqual(data['setting_type'], 'string')
        self.assertIn('user', data)
    
    def test_create_user_setting_with_context(self):
        """Testa criação de configuração de usuário com contexto"""
        request = APIRequestFactory().post('/')
        request.user = self.user
        
        data = {
            'key': 'new_user_setting',
            'value': 'new_user_value',
            'setting_type': 'string',
            'description': 'New user setting'
        }
        
        serializer = UserSettingSerializer(
            data=data,
            context={'request': request}
        )
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())
        
        user_setting = serializer.save(user=self.user)
        self.assertEqual(user_setting.user, self.user)
        self.assertEqual(user_setting.key, 'new_user_setting')
    
    def test_unique_key_per_user_validation(self):
        """Testa validação de chave única por usuário"""
        request = APIRequestFactory().post('/')
        request.user = self.user
        
        data = {
            'key': 'user_test_setting',  # Chave já existe para este usuário
            'value': 'another_value',
            'setting_type': 'string'
        }
        
        serializer = UserSettingSerializer(
            data=data,
            context={'request': request}
        )
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())
        # A validação de unicidade deve ser feita no nível do modelo/banco
        with self.assertRaises(Exception):
            serializer.save(user=self.user)


class SettingTemplateSerializerTest(TestCase):
    """Testes para o serializer de templates de configuração"""
    
    def setUp(self):
        self.template = SettingTemplate.objects.create(
            key='template_setting',
            name='Template Setting',
            description='A template setting',
            setting_type='string',
            default_value='default',
            scope='global',
            category='template'
        )
    
    def test_serialize_setting_template(self):
        """Testa serialização de template de configuração"""
        serializer = SettingTemplateSerializer(self.template)
        data = serializer.data
        
        self.assertEqual(data['key'], 'template_setting')
        self.assertEqual(data['name'], 'Template Setting')
        self.assertEqual(data['setting_type'], 'string')
        self.assertEqual(data['default_value'], 'default')
        self.assertEqual(data['scope'], 'global')
    
    def test_deserialize_valid_template(self):
        """Testa deserialização válida de template"""
        data = {
            'key': 'new_template',
            'name': 'New Template',
            'description': 'A new template',
            'setting_type': 'integer',
            'default_value': '100',
            'scope': 'account',
            'category': 'new'
        }
        
        serializer = SettingTemplateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        template = serializer.save()
        self.assertEqual(template.key, 'new_template')
        self.assertEqual(template.scope, 'account')
    
    def test_validation_rules_serialization(self):
        """Testa serialização de regras de validação"""
        validation_rules = {
            'min_length': 5,
            'max_length': 100,
            'pattern': r'^[a-zA-Z0-9]+$'
        }
        
        template = SettingTemplate.objects.create(
            key='validated_setting',
            name='Validated Setting',
            description='A setting with validation rules',
            setting_type='string',
            scope='user',
            category='test',
            validation_rules=validation_rules
        )
        
        serializer = SettingTemplateSerializer(template)
        data = serializer.data
        
        self.assertEqual(data['key'], 'validated_setting')
        self.assertEqual(data['validation_rules'], validation_rules)
    
    def test_choices_serialization(self):
        """Testa serialização de opções de escolha"""
        choices = ['option1', 'option2', 'option3']
        validation_rules = {'choices': choices}
        
        template = SettingTemplate.objects.create(
            key='choice_setting',
            name='Choice Setting',
            description='A setting with choices',
            setting_type='string',
            scope='global',
            category='test',
            validation_rules=validation_rules
        )
        
        serializer = SettingTemplateSerializer(template)
        data = serializer.data
        
        self.assertEqual(data['key'], 'choice_setting')
        self.assertEqual(data['validation_rules']['choices'], choices)


class SerializerValidationTest(TestCase):
    """Testes para validações específicas dos serializers"""
    
    def test_setting_type_validation(self):
        """Testa validação de tipos de configuração"""
        valid_types = ['string', 'integer', 'float', 'boolean', 'json', 'text']
        
        for setting_type in valid_types:
            data = {
                'key': f'test_{setting_type}',
                'value': 'test_value',
                'setting_type': setting_type
            }
            
            serializer = GlobalSettingSerializer(data=data)
            self.assertTrue(serializer.is_valid(), 
                          f'Setting type {setting_type} should be valid')
    
    def test_invalid_setting_type_validation(self):
        """Testa validação de tipo inválido"""
        data = {
            'key': 'test_invalid',
            'value': 'test_value',
            'setting_type': 'invalid_type'
        }
        
        serializer = GlobalSettingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('setting_type', serializer.errors)
    
    def test_key_format_validation(self):
        """Testa validação de formato de chave"""
        # Chaves válidas
        valid_keys = ['valid_key', 'valid-key', 'valid.key', 'valid_key_123']
        
        for key in valid_keys:
            data = {
                'key': key,
                'value': 'test_value',
                'setting_type': 'string'
            }
            
            serializer = GlobalSettingSerializer(data=data)
            self.assertTrue(serializer.is_valid(), 
                          f'Key {key} should be valid')
    
    def test_value_type_consistency(self):
        """Testa consistência entre valor e tipo"""
        # Teste com valor integer válido
        data = {
            'key': 'int_test',
            'value': '42',
            'setting_type': 'integer'
        }
        serializer = GlobalSettingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Teste com valor boolean válido
        data = {
            'key': 'bool_test',
            'value': 'true',
            'setting_type': 'boolean'
        }
        serializer = GlobalSettingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Teste com valor float válido
        data = {
            'key': 'float_test',
            'value': '3.14',
            'setting_type': 'float'
        }
        serializer = GlobalSettingSerializer(data=data)
        self.assertTrue(serializer.is_valid())