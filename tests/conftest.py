import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from accounts.models import Account, AccountMembership
from users.models import UserProfile
import factory
from factory.django import DjangoModelFactory
from factory import Faker

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup database for tests."""
    pass


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(user):
    """Authenticated Django test client."""
    client = Client()
    client.force_login(user)
    return client


class AccountFactory(DjangoModelFactory):
    """Factory for Account model."""
    class Meta:
        model = Account
    
    name = Faker('company')
    slug = Faker('slug')
    plan = 'basic'
    status = 'active'
    max_users = 10
    max_storage_gb = 5
    owner = factory.SubFactory('tests.conftest.UserFactory')


class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    class Meta:
        model = User
    
    username = Faker('user_name')
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    is_active = True


class UserProfileFactory(DjangoModelFactory):
    """Factory for UserProfile model."""
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    account = factory.SubFactory(AccountFactory)
    role = 'member'
    phone = Faker('phone_number')
    bio = Faker('text')


@pytest.fixture
def account():
    """Create a test account."""
    return AccountFactory()


@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def user_profile(user, account):
    """Create a test user profile."""
    return UserProfileFactory(user=user, account=account)


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def owner_user(account):
    """Create an account owner user."""
    user = UserFactory()
    UserProfileFactory(user=user, account=account, role='owner')
    return user


@pytest.fixture
def member_user(account):
    """Create an account member user."""
    user = UserFactory()
    UserProfileFactory(user=user, account=account, role='member')
    return user