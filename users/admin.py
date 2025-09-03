from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline para o perfil do usuário"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Perfil')
    fields = (
        'bio', 'birth_date', 'website', 'company', 'job_title', 'location',
        'timezone', 'language', 'email_notifications', 'sms_notifications', 
        'push_notifications'
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin customizado para o modelo User"""
    
    inlines = (UserProfileInline,)
    
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'status', 
        'is_active', 'email_verified', 'phone_verified', 'created_at'
    )
    
    list_filter = (
        'status', 'is_active', 'is_staff', 'is_superuser', 
        'email_verified', 'phone_verified', 'created_at'
    )
    
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    
    ordering = ('-created_at',)
    
    readonly_fields = (
        'created_at', 'updated_at', 'last_login', 'date_joined',
        'failed_login_attempts', 'locked_until', 'last_login_ip'
    )
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Informações Pessoais'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        (_('Permissões'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'status',
                'groups', 'user_permissions'
            )
        }),
        (_('Verificações'), {
            'fields': ('email_verified', 'phone_verified')
        }),
        (_('Segurança'), {
            'fields': (
                'failed_login_attempts', 'locked_until', 'last_login_ip'
            ),
            'classes': ('collapse',)
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name', 
                'password1', 'password2', 'status'
            ),
        }),
    )
    
    actions = ['activate_users', 'deactivate_users', 'verify_emails']
    
    def activate_users(self, request, queryset):
        """Ação para ativar usuários selecionados"""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(
            request, 
            f'{updated} usuário(s) ativado(s) com sucesso.'
        )
    activate_users.short_description = _('Ativar usuários selecionados')
    
    def deactivate_users(self, request, queryset):
        """Ação para desativar usuários selecionados"""
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(
            request, 
            f'{updated} usuário(s) desativado(s) com sucesso.'
        )
    deactivate_users.short_description = _('Desativar usuários selecionados')
    
    def verify_emails(self, request, queryset):
        """Ação para verificar emails dos usuários selecionados"""
        updated = queryset.update(email_verified=True)
        self.message_user(
            request, 
            f'{updated} email(s) verificado(s) com sucesso.'
        )
    verify_emails.short_description = _('Verificar emails selecionados')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para o modelo UserProfile"""
    
    list_display = (
        'user', 'company', 'job_title', 'location', 'language', 
        'email_notifications', 'created_at'
    )
    
    list_filter = (
        'language', 'timezone', 'email_notifications', 
        'sms_notifications', 'push_notifications', 'created_at'
    )
    
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'company', 'job_title', 'location'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('user', 'bio', 'birth_date')
        }),
        (_('Informações Profissionais'), {
            'fields': ('company', 'job_title', 'website')
        }),
        (_('Localização e Idioma'), {
            'fields': ('location', 'timezone', 'language')
        }),
        (_('Preferências de Notificação'), {
            'fields': (
                'email_notifications', 'sms_notifications', 'push_notifications'
            )
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
