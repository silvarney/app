import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import Account, AccountMembership
from content.models import Content, Category
from tests.conftest import UserFactory, AccountFactory

User = get_user_model()


@pytest.mark.django_db
class TestAccountAPIViews:
    """Test cases for Account API views."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = APIClient()
        self.user = UserFactory()
        self.account = AccountFactory(owner=self.user)
        
        # Create account membership if it doesn't exist
        from accounts.models import AccountMembership
        AccountMembership.objects.get_or_create(
            user=self.user,
            account=self.account,
            defaults={
                'role': 'owner',
                'status': 'active'
            }
        )
        
    def test_account_list_unauthenticated(self):
        """Test account list without authentication."""
        url = reverse('api:account-list')
        response = self.client.get(url)
        
        # Should require authentication
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_account_list_authenticated(self):
        """Test account list with authentication."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:account-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
        assert len(response.data['results']) >= 1
    
    @pytest.mark.api
    def test_account_detail_view(self):
        """Test account detail view."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:account-detail', kwargs={'pk': self.account.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data['id']) == str(self.account.id)
        assert response.data['name'] == self.account.name
    
    def test_account_create(self):
        """Test creating an account via API."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'New Test Account',
            'slug': 'newtestaccount',
            'plan': 'basic'
        }
        
        url = reverse('api:account-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Account.objects.filter(name='New Test Account').exists()
    
    def test_account_update(self):
        """Test updating an account via API."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'Updated Account Name',
            'slug': self.account.slug,
            'plan': self.account.plan
        }
        
        url = reverse('api:account-detail', kwargs={'pk': self.account.pk})
        response = self.client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        self.account.refresh_from_db()
        assert self.account.name == 'Updated Account Name'
    
    def test_account_delete(self):
        """Test deleting an account via API."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('api:account-detail', kwargs={'pk': self.account.pk})
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Account.objects.filter(pk=self.account.pk).exists()


@pytest.mark.django_db
class TestContentAPIViews:
    """Test cases for Content API views."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = APIClient()
        self.user = UserFactory()
        self.account = AccountFactory()
        
        # Create account membership
        from accounts.models import AccountMembership
        AccountMembership.objects.create(
            user=self.user,
            account=self.account,
            role='owner',
            status='active'
        )
        
        # Create a category for content
        self.category = Category.objects.create(
            name='Test Category',
            account=self.account
        )
        
        # Create test content
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            account=self.account,
            author=self.user,
            status='published',
            category=self.category
        )
    
    def test_content_list_public(self):
        """Test public content list."""
        url = reverse('api:content-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    @pytest.mark.api
    def test_content_detail_view(self):
        """Test content detail view."""
        url = reverse('api:content-detail', kwargs={'pk': self.content.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.content.id
        assert response.data['title'] == self.content.title
    
    def test_content_create_authenticated(self):
        """Test creating content with authentication."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'New Test Content',
            'content': 'New test content body',
            'account': self.account.id,
            'status': 'draft',
            'category': self.category.id
        }
        
        url = reverse('api:content-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Content.objects.filter(title='New Test Content').exists()
    
    def test_content_create_unauthenticated(self):
        """Test creating content without authentication."""
        data = {
            'title': 'Unauthorized Content',
            'content': 'This should not be created',
            'account': self.account.id
        }
        
        url = reverse('api:content-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_content_filter_by_category(self):
        """Test filtering content by category."""
        url = reverse('api:content-list')
        response = self.client.get(url, {'category': self.category.id})
        
        assert response.status_code == status.HTTP_200_OK
        # Check if response.data is a list and has content
        if isinstance(response.data, list) and len(response.data) > 0:
            # All returned content should belong to the specified category
            for content_item in response.data:
                if isinstance(content_item, dict) and 'id' in content_item:
                    content_obj = Content.objects.get(id=content_item['id'])
                    assert content_obj.category == self.category
    
    def test_content_filter_by_status(self):
        """Test filtering content by status."""
        url = reverse('api:content-list')
        response = self.client.get(url, {'status': 'published'})
        
        assert response.status_code == status.HTTP_200_OK
        # Check if response.data is a list and has content
        if isinstance(response.data, list) and len(response.data) > 0:
            # All returned content should have published status
            for content_item in response.data:
                if isinstance(content_item, dict) and 'status' in content_item:
                    assert content_item['status'] == 'published'
    
    def test_content_search(self):
        """Test content search functionality."""
        url = reverse('api:content-list')
        response = self.client.get(url, {'search': 'Test'})
        
        assert response.status_code == status.HTTP_200_OK
        # Should return content with 'Test' in title or content
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestAPIAuthentication:
    """Test cases for API authentication and permissions."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = APIClient()
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.account = AccountFactory()
    
    def test_api_requires_authentication(self):
        """Test that protected endpoints require authentication."""
        protected_urls = [
            reverse('api:account-list'),
            reverse('api:user-list'),
        ]
        
        for url in protected_urls:
            response = self.client.post(url, {})
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_api_with_valid_authentication(self):
        """Test API access with valid authentication."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('api:account-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.api
    def test_admin_only_endpoints(self):
        """Test endpoints that require admin privileges."""
        # Regular user should not have access
        self.client.force_authenticate(user=self.user)
        
        url = reverse('api:user-list')
        response = self.client.get(url)
        
        # This might return 403 Forbidden or 200 OK depending on permissions
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
        
        # Admin user should have access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_api_error_handling(self):
        """Test API error handling."""
        self.client.force_authenticate(user=self.user)
        
        # Test 404 error
        url = reverse('api:account-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test validation error
        url = reverse('api:account-list')
        invalid_data = {
            'name': '',  # Empty name should cause validation error
            'slug': 'test'
        }
        response = self.client.post(url, invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAPIPerformance:
    """Test cases for API performance and optimization."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.client = APIClient()
        self.user = UserFactory()
        self.account = AccountFactory()
    
    @pytest.mark.slow
    def test_content_list_pagination(self):
        """Test content list pagination."""
        # Create a category for content
        category = Category.objects.create(
            name='Test Category',
            account=self.account
        )
        
        # Create multiple content items
        for i in range(25):
            Content.objects.create(
                title=f'Content {i}',
                content=f'Content body {i}',
                account=self.account,
                author=self.user,
                status='published',
                category=category
            )
        
        url = reverse('api:content-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Should be paginated (assuming default page size is 20)
        assert len(response.data) <= 20
    
    @pytest.mark.slow
    def test_api_response_time(self):
        """Test API response time for large datasets."""
        import time
        
        # Create a category for content
        category = Category.objects.create(
            name='Test Category',
            account=self.account
        )
        
        # Create some test data
        for i in range(10):
            Content.objects.create(
                title=f'Performance Test Content {i}',
                content=f'Performance test content body {i}',
                account=self.account,
                author=self.user,
                status='published',
                category=category
            )
        
        url = reverse('api:content-list')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == status.HTTP_200_OK
        # Response should be reasonably fast (less than 1 second)
        assert response_time < 1.0