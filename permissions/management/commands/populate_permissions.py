from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from permissions.models import Permission, Role
from accounts.models import Account
from users.models import User
from content.models import Content, Category, Tag
from domains.models import Domain


class Command(BaseCommand):
    help = 'Populate default permissions and roles for the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of permissions even if they exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting permission population...'))
        
        # Define default permissions
        default_permissions = [
            # Content Management
            {
                'name': 'Can create content',
                'codename': 'create_content',
                'description': 'Permission to create new content',
                'permission_type': 'create',
                'resource': 'content',
                'content_type': ContentType.objects.get_for_model(Content),
                'category': 'content_management'
            },
            {
                'name': 'Can view content',
                'codename': 'view_content',
                'description': 'Permission to view content',
                'permission_type': 'read',
                'resource': 'content',
                'content_type': ContentType.objects.get_for_model(Content),
                'category': 'content_management'
            },
            {
                'name': 'Can edit content',
                'codename': 'edit_content',
                'description': 'Permission to edit existing content',
                'permission_type': 'update',
                'resource': 'content',
                'content_type': ContentType.objects.get_for_model(Content),
                'category': 'content_management'
            },
            {
                'name': 'Can delete content',
                'codename': 'delete_content',
                'description': 'Permission to delete content',
                'permission_type': 'delete',
                'resource': 'content',
                'content_type': ContentType.objects.get_for_model(Content),
                'category': 'content_management'
            },
            {
                'name': 'Can publish content',
                'codename': 'publish_content',
                'description': 'Permission to publish/unpublish content',
                'permission_type': 'manage',
                'resource': 'content',
                'content_type': ContentType.objects.get_for_model(Content),
                'category': 'content_management'
            },
            
            # Category Management
            {
                'name': 'Can manage categories',
                'codename': 'manage_categories',
                'description': 'Permission to manage content categories',
                'permission_type': 'manage',
                'resource': 'category',
                'content_type': ContentType.objects.get_for_model(Category),
                'category': 'content_management'
            },
            
            # Tag Management
            {
                'name': 'Can manage tags',
                'codename': 'manage_tags',
                'description': 'Permission to manage content tags',
                'permission_type': 'manage',
                'resource': 'tag',
                'content_type': ContentType.objects.get_for_model(Tag),
                'category': 'content_management'
            },
            
            # Domain Management
            {
                'name': 'Can create domains',
                'codename': 'create_domain',
                'description': 'Permission to add new domains',
                'permission_type': 'create',
                'resource': 'domain',
                'content_type': ContentType.objects.get_for_model(Domain),
                'category': 'domain_management'
            },
            {
                'name': 'Can view domains',
                'codename': 'view_domain',
                'description': 'Permission to view domains',
                'permission_type': 'read',
                'resource': 'domain',
                'content_type': ContentType.objects.get_for_model(Domain),
                'category': 'domain_management'
            },
            {
                'name': 'Can edit domains',
                'codename': 'edit_domain',
                'description': 'Permission to edit domain settings',
                'permission_type': 'update',
                'resource': 'domain',
                'content_type': ContentType.objects.get_for_model(Domain),
                'category': 'domain_management'
            },
            {
                'name': 'Can delete domains',
                'codename': 'delete_domain',
                'description': 'Permission to delete domains',
                'permission_type': 'delete',
                'resource': 'domain',
                'content_type': ContentType.objects.get_for_model(Domain),
                'category': 'domain_management'
            },
            {
                'name': 'Can verify domains',
                'codename': 'verify_domain',
                'description': 'Permission to verify domain ownership',
                'permission_type': 'manage',
                'resource': 'domain',
                'content_type': ContentType.objects.get_for_model(Domain),
                'category': 'domain_management'
            },
            
            # User Management
            {
                'name': 'Can manage users',
                'codename': 'manage_users',
                'description': 'Permission to manage account users',
                'permission_type': 'manage',
                'resource': 'user',
                'content_type': ContentType.objects.get_for_model(User),
                'category': 'user_management'
            },
            
            # Account Management
            {
                'name': 'Can manage account',
                'codename': 'manage_account',
                'description': 'Permission to manage account settings',
                'permission_type': 'admin',
                'resource': 'account',
                'content_type': ContentType.objects.get_for_model(Account),
                'category': 'account_management'
            },
        ]
        
        # Create permissions
        created_permissions = []
        for perm_data in default_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            if created or force:
                if force and not created:
                    for key, value in perm_data.items():
                        setattr(permission, key, value)
                    permission.save()
                created_permissions.append(permission)
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {permission.name}')
                )
        
        # Define default roles
        default_roles = [
            {
                'name': 'Content Editor',
                'codename': 'content_editor',
                'description': 'Can create, edit and manage content',
                'role_type': 'custom',
                'priority': 100,
                'permissions': [
                    'create_content', 'view_content', 'edit_content',
                    'manage_categories', 'manage_tags'
                ]
            },
            {
                'name': 'Content Publisher',
                'codename': 'content_publisher',
                'description': 'Can publish and manage all content',
                'role_type': 'custom',
                'priority': 200,
                'permissions': [
                    'create_content', 'view_content', 'edit_content',
                    'delete_content', 'publish_content',
                    'manage_categories', 'manage_tags'
                ]
            },
            {
                'name': 'Domain Manager',
                'codename': 'domain_manager',
                'description': 'Can manage domains and configurations',
                'role_type': 'custom',
                'priority': 150,
                'permissions': [
                    'create_domain', 'view_domain', 'edit_domain',
                    'delete_domain', 'verify_domain'
                ]
            },
            {
                'name': 'Account Admin',
                'codename': 'account_admin',
                'description': 'Full administrative access to account',
                'role_type': 'admin',
                'priority': 1000,
                'permissions': [
                    'create_content', 'view_content', 'edit_content',
                    'delete_content', 'publish_content',
                    'manage_categories', 'manage_tags',
                    'create_domain', 'view_domain', 'edit_domain',
                    'delete_domain', 'verify_domain',
                    'manage_users', 'manage_account'
                ]
            },
        ]
        
        # Create roles (system-wide, no account)
        for role_data in default_roles:
            permissions_codenames = role_data.pop('permissions')
            role, created = Role.objects.get_or_create(
                codename=role_data['codename'],
                account=None,  # System role
                defaults={**role_data, 'is_system': True}
            )
            
            if created or force:
                if force and not created:
                    for key, value in role_data.items():
                        setattr(role, key, value)
                    role.save()
                
                # Add permissions to role
                role_permissions = Permission.objects.filter(
                    codename__in=permissions_codenames
                )
                role.permissions.set(role_permissions)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.name} with {role_permissions.count()} permissions')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated {len(created_permissions)} permissions and {len(default_roles)} roles'
            )
        )