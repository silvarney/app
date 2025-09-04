import pytest
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import Account
from settings.models import GlobalSetting, AccountSetting, UserSetting
from permissions.models import Permission, Role, UserRole

User = get_user_model()


class GlobalSettingsAPITest(APITestCase):
    """Testes para a API de configurações globais"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Criar usuário admin
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        # Criar usuário comum
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Criar configurações globais de teste
        self.global_setting1 = GlobalSetting.objects.create(
            key='test_setting_1',
            value='value1',
            setting_type='string',
            description='Test setting 1',
            category='test',
            is_public=True
        )
        
        self.global_setting2 = GlobalSetting.objects.create(
            key='test_setting_2',
            value='42',
            setting_type='integer',
            description='Test setting 2',
            category='test',
            is_public=False
        )
    
    def test_list_global_settings_as_admin(self):
        """Testa listagem de configurações globais como admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('settings:global-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_list_global_settings_as_regular_user(self):
        """Testa listagem de configurações globais como usuário comum"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('settings:global-list')
        response = self.client.get(url)
        
        # Usuário comum só deve ver configurações públicas
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'test_setting_1')
    
    def test_list_global_settings_unauthenticated(self):
        """Testa listagem de configurações globais sem autenticação"""
        url = reverse('settings:global-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_global_setting_as_admin(self):
        """Testa criação de configuração global como admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('settings:global-list')
        data = {
            'key': 'new_setting',
            'value': 'new_value',
            'setting_type': 'string',
            'description': 'New test setting',
            'category': 'test'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GlobalSetting.objects.filter(key='new_setting').exists())
    
    def test_create_global_setting_as_regular_user(self):
        """Testa criação de configuração global como usuário comum"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('settings:global-list')
        data = {
            'key': 'unauthorized_setting',
            'value': 'value',
            'setting_type': 'string'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_global_setting_as_admin(self):
        """Testa atualização de configuração global como admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('settings:global-detail', kwargs={'pk': self.global_setting1.pk})
        data = {
            'key': 'test_setting_1',
            'value': 'updated_value',
            'setting_type': 'string',
            'description': 'Updated description',
            'category': 'test'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.global_setting1.refresh_from_db()
        self.assertEqual(self.global_setting1.value, 'updated_value')
    
    def test_delete_global_setting_as_admin(self):
        """Testa exclusão de configuração global como admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('settings:global-detail', kwargs={'pk': self.global_setting1.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GlobalSetting.objects.filter(pk=self.global_setting1.pk).exists())


class AccountSettingsAPITest(APITestCase):
    """Testes para a API de configurações de conta"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Criar conta
        self.account = Account.objects.create(
            name='Test Account',
            slug='test-account'
        )
        
        # Criar usuário da conta
        self.account_user = User.objects.create_user(
            username='accountuser',
            email='account@example.com',
            password='accountpass123'
        )
        self.account_user.account = self.account
        self.account_user.save()
        
        # Criar usuário de outra conta
        self.other_account = Account.objects.create(
            name='Other Account',
            slug='other-account'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.other_user.account = self.other_account
        self.other_user.save()
        
        # Criar configurações de conta
        self.account_setting = AccountSetting.objects.create(
            account=self.account,
            key='account_test_setting',
            value='account_value',
            setting_type='string',
            description='Account test setting'
        )
    
    def test_list_account_settings_as_account_member(self):
        """Testa listagem de configurações da conta como membro"""
        self.client.force_authenticate(user=self.account_user)
        url = reverse('settings:account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'account_test_setting')
    
    def test_list_account_settings_as_other_account_member(self):
        """Testa listagem de configurações da conta como membro de outra conta"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('settings:account-list')
        response = self.client.get(url)
        
        # Não deve ver configurações de outras contas
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_account_setting_as_account_member(self):
        """Testa criação de configuração de conta como membro"""
        self.client.force_authenticate(user=self.account_user)
        url = reverse('settings:account-list')
        data = {
            'key': 'new_account_setting',
            'value': 'new_account_value',
            'setting_type': 'string',
            'description': 'New account setting'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AccountSetting.objects.filter(
                account=self.account,
                key='new_account_setting'
            ).exists()
        )


class UserSettingsAPITest(APITestCase):
    """Testes para a API de configurações de usuário"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Criar usuários
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user1pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2pass123'
        )
        
        # Criar configurações de usuário
        self.user_setting = UserSetting.objects.create(
            user=self.user1,
            key='user_test_setting',
            value='user_value',
            setting_type='string',
            description='User test setting'
        )
    
    def test_list_user_settings_as_owner(self):
        """Testa listagem de configurações do próprio usuário"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('settings:user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'user_test_setting')
    
    def test_list_user_settings_as_other_user(self):
        """Testa listagem de configurações como outro usuário"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('settings:user-list')
        response = self.client.get(url)
        
        # Não deve ver configurações de outros usuários
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_user_setting_as_owner(self):
        """Testa criação de configuração de usuário"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('settings:user-list')
        data = {
            'key': 'new_user_setting',
            'value': 'new_user_value',
            'setting_type': 'string',
            'description': 'New user setting'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserSetting.objects.filter(
                user=self.user1,
                key='new_user_setting'
            ).exists()
        )
    
    def test_update_user_setting_as_owner(self):
        """Testa atualização de configuração do próprio usuário"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('settings:user-detail', kwargs={'pk': self.user_setting.pk})
        data = {
            'key': 'user_test_setting',
            'value': 'updated_user_value',
            'setting_type': 'string',
            'description': 'Updated user setting'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_setting.refresh_from_db()
        self.assertEqual(self.user_setting.value, 'updated_user_value')
    
    def test_update_user_setting_as_other_user(self):
        """Testa atualização de configuração de outro usuário"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('settings:user-detail', kwargs={'pk': self.user_setting.pk})
        data = {
            'key': 'user_test_setting',
            'value': 'unauthorized_update',
            'setting_type': 'string'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SettingsViewTest(TestCase):
    """Testes para a view de configurações do painel do usuário"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = Account.objects.create(
            name='Test Account',
            slug='test-account'
        )
        self.user.account = self.account
        self.user.save()
    
    def test_settings_view_authenticated(self):
        """Testa acesso à página de configurações autenticado"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('user_panel:settings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configurações')
        self.assertContains(response, 'Vue.js')
    
    def test_settings_view_unauthenticated(self):
        """Testa acesso à página de configurações sem autenticação"""
        url = reverse('user_panel:settings')
        response = self.client.get(url)
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
    
    def test_settings_view_context(self):
        """Testa o contexto passado para a view de configurações"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('user_panel:settings')
        response = self.client.get(url)
        
        self.assertIn('user', response.context)
        self.assertIn('canManageAccount', response.context)
        self.assertIn('isAdmin', response.context)
        self.assertEqual(response.context['user'], self.user)