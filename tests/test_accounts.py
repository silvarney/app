import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import Account, AccountMembership
from tests.conftest import AccountFactory, UserFactory


@pytest.mark.django_db
class TestAccountModel:
    """Test cases for Account model."""


    def test_account_creation(self):
        """Test creating an account."""
        user = UserFactory()
        account = AccountFactory(
            name="Test Company",
            slug="testcompany",
            plan="basic",
            owner=user
        )
        assert account.name == "Test Company"
        assert account.slug == "testcompany"
        assert account.plan == "basic"
        assert account.is_active is True
        assert account.created_at is not None
    
    def test_account_str_representation(self):
        """Test account string representation."""
        account = AccountFactory(name="Test Account")
        assert str(account) == "Test Account"
    
    def test_slug_uniqueness(self):
        """Test that slugs must be unique."""
        user1 = UserFactory()
        user2 = UserFactory()
        AccountFactory(slug="unique", owner=user1)
        
        with pytest.raises(IntegrityError):
            AccountFactory(slug="unique", owner=user2)
    
    @pytest.mark.unit
    def test_slug_validation(self):
        """Test slug validation."""
        user = UserFactory()
        # Test invalid slug with spaces
        account = Account(
            name="Test",
            slug="invalid slug",
            plan="basic",
            owner=user
        )
        with pytest.raises(ValidationError):
            account.full_clean()
    
    def test_account_plan_field(self):
        """Test account plan field."""
        user = UserFactory()
        account = AccountFactory(plan="premium", owner=user)
        assert account.plan == "premium"
    
    @pytest.mark.models
    def test_account_status_change(self):
        """Test account status change functionality."""
        user = UserFactory()
        account = AccountFactory(status='active', owner=user)
        assert account.is_active is True
        
        # Change status to suspended
        account.status = 'suspended'
        account.save()
        
        account.refresh_from_db()
        assert account.is_active is False
    
    def test_account_metadata_fields(self):
        """Test account metadata fields."""
        account = AccountFactory()
        assert account.created_at is not None
        assert account.updated_at is not None
        
        # Test that updated_at changes on save
        original_updated = account.updated_at
        account.name = "Updated Name"
        account.save()
        account.refresh_from_db()
        
        assert account.updated_at > original_updated


@pytest.mark.django_db
class TestAccountMembershipModel:
    """Test cases for AccountMembership model."""
    
    @pytest.mark.models
    def test_membership_creation(self):
        """Test creating an account membership."""
        owner = UserFactory()
        member_user = UserFactory()
        account = AccountFactory(owner=owner)
        
        membership = AccountMembership.objects.create(
            account=account,
            user=member_user,
            role='member',
            status='pending'
        )
        
        assert membership.account == account
        assert membership.user == member_user
        assert membership.role == 'member'
        assert membership.status == 'pending'
    
    @pytest.mark.models
    def test_membership_str_representation(self):
        """Test membership string representation."""
        owner = UserFactory()
        member_user = UserFactory(first_name='John', last_name='Doe')
        account = AccountFactory(name='Test Account', owner=owner)
        
        membership = AccountMembership.objects.create(
            account=account,
            user=member_user,
            role='admin',
            status='active'
        )
        
        expected = f'{member_user.get_full_name()} - {account.name}'
        assert str(membership) == expected