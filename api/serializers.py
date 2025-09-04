from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import Account, AccountMembership, AccountInvitation
from permissions.models import Permission, Role, UserRole, UserPermission
from payments.models import Plan, Subscription, Payment, Invoice
from content.models import Category, Tag, Content, ContentAttachment
from domains.models import Domain, DomainConfiguration, DomainVerificationLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class AccountSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'slug', 'description', 'company_name', 'website',
            'plan', 'status', 'owner', 'member_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.memberships.filter(status='active').count()


class AccountMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account = AccountSerializer(read_only=True)
    
    class Meta:
        model = AccountMembership
        fields = [
            'id', 'account', 'user', 'role', 'status', 'can_invite_users',
            'can_manage_billing', 'can_manage_settings', 'can_view_analytics',
            'joined_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            'id', 'name', 'codename', 'description', 'permission_type',
            'category', 'resource', 'is_active'
        ]
        read_only_fields = ['id']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'codename', 'description', 'priority',
            'is_system_role', 'is_active', 'permissions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price', 'billing_cycle',
            'max_users', 'max_storage_gb', 'max_api_calls', 'features',
            'is_active', 'stripe_price_id'
        ]
        read_only_fields = ['id']


class SubscriptionSerializer(serializers.ModelSerializer):
    account = AccountSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'account', 'plan', 'status', 'stripe_subscription_id',
            'current_period_start', 'current_period_end', 'trial_end',
            'cancel_at_period_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'amount', 'currency', 'status',
            'stripe_payment_intent_id', 'payment_method', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar']
        read_only_fields = ['id', 'email']


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem.")
        return attrs


# Content Management Serializers
class CategorySerializer(serializers.ModelSerializer):
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'account',
            'is_active', 'content_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_content_count(self, obj):
        return obj.content_set.filter(status='published').count()


class TagSerializer(serializers.ModelSerializer):
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'account',
            'is_active', 'content_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_content_count(self, obj):
        return obj.content_set.filter(status='published').count()


class ContentAttachmentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentAttachment
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_size_display',
            'file_type', 'alt_text', 'caption', 'order', 'uploaded_at'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at']
    
    def get_file_size_display(self, obj):
        """Retorna o tamanho do arquivo em formato legível"""
        if obj.file_size:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024.0:
                    return f"{obj.file_size:.1f} {unit}"
                obj.file_size /= 1024.0
            return f"{obj.file_size:.1f} TB"
        return "0 B"


class ContentSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    attachments = ContentAttachmentSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    
    # Campos para escrita
    category_id = serializers.IntegerField(write_only=True, required=False)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'status',
            'content_type', 'featured_image', 'meta_title', 'meta_description',
            'category', 'tags', 'attachments', 'author', 'account',
            'is_featured', 'views_count', 'published_at',
            'created_at', 'updated_at',
            # Write-only fields
            'category_id', 'tag_ids'
        ]
        read_only_fields = [
            'id', 'slug', 'author', 'account', 'view_count',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        content = super().create(validated_data)
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, account=content.account)
            content.tags.set(tags)
        
        return content
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        content = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids, account=content.account)
            content.tags.set(tags)
        
        return content


# Domain Management Serializers
class DomainConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainConfiguration
        fields = [
            'id', 'cache_enabled', 'cache_ttl', 'default_title',
            'default_description', 'robots_txt', 'google_analytics_id',
            'google_tag_manager_id', 'facebook_pixel_id', 'force_https',
            'hsts_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DomainVerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainVerificationLog
        fields = [
            'id', 'verification_method', 'status', 'details', 'checked_at'
        ]
        read_only_fields = ['id', 'checked_at']


class DomainSerializer(serializers.ModelSerializer):
    configuration = DomainConfigurationSerializer(read_only=True)
    verification_logs = DomainVerificationLogSerializer(many=True, read_only=True)
    verification_instructions = serializers.ReadOnlyField()
    ssl_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Domain
        fields = [
            'id', 'name', 'domain_type', 'account', 'status', 'verification_token',
            'verification_method', 'ssl_enabled', 'ssl_expires_at', 'redirect_to',
            'redirect_type', 'is_active', 'is_primary', 'verified_at',
            'last_checked_at', 'created_at', 'updated_at',
            # Related fields
            'configuration', 'verification_logs', 'verification_instructions',
            'ssl_status_display'
        ]
        read_only_fields = [
            'id', 'verification_token', 'verified_at', 'last_checked_at',
            'created_at', 'updated_at'
        ]
    
    def get_ssl_status_display(self, obj):
        if obj.ssl_enabled:
            if obj.check_ssl_expiry():
                return 'expired'
            return 'active'
        return 'disabled'