from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Account, AccountMembership, AccountInvitation


class AccountMembershipInline(admin.TabularInline):
    model = AccountMembership
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'joined_at')
    fields = (
        'user', 'role', 'status', 'can_invite_users', 'can_manage_billing',
        'can_manage_settings', 'can_view_analytics', 'invited_by', 'joined_at'
    )


class AccountInvitationInline(admin.TabularInline):
    model = AccountInvitation
    extra = 0
    readonly_fields = ('token', 'created_at', 'expires_at', 'accepted_at')
    fields = ('email', 'role', 'status', 'invited_by', 'expires_at', 'accepted_at')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'owner', 'plan', 'status', 'current_users_count',
        'max_users', 'trial_ends_at', 'created_at'
    )
    list_filter = ('plan', 'status', 'created_at', 'trial_ends_at')
    search_fields = ('name', 'slug', 'company_name', 'owner__username', 'owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'current_users_count')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'slug', 'description', 'owner')
        }),
        ('Informações da Empresa', {
            'fields': ('company_name', 'cnpj', 'cpf', 'website', 'phone'),
            'classes': ('collapse',)
        }),
        ('Endereço', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state',
                'postal_code', 'country'
            ),
            'classes': ('collapse',)
        }),
        ('Plano e Limites', {
            'fields': (
                'plan', 'status', 'max_users', 'max_storage_gb', 'max_domains',
                'current_users_count'
            )
        }),
        ('Configurações', {
            'fields': ('timezone', 'language'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('trial_ends_at', 'subscription_ends_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [AccountMembershipInline, AccountInvitationInline]
    
    def current_users_count(self, obj):
        return obj.current_users_count
    current_users_count.short_description = 'Usuários Ativos'
    
    actions = ['activate_accounts', 'suspend_accounts', 'extend_trial']
    
    def activate_accounts(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} contas foram ativadas.')
    activate_accounts.short_description = 'Ativar contas selecionadas'
    
    def suspend_accounts(self, request, queryset):
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} contas foram suspensas.')
    suspend_accounts.short_description = 'Suspender contas selecionadas'
    
    def extend_trial(self, request, queryset):
        from datetime import timedelta
        for account in queryset:
            if account.trial_ends_at:
                account.trial_ends_at += timedelta(days=30)
                account.save()
        self.message_user(request, f'Trial estendido por 30 dias para {queryset.count()} contas.')
    extend_trial.short_description = 'Estender trial por 30 dias'


@admin.register(AccountMembership)
class AccountMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'account', 'role', 'status', 'can_invite_users',
        'can_manage_billing', 'joined_at', 'created_at'
    )
    list_filter = ('role', 'status', 'can_invite_users', 'can_manage_billing', 'created_at')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'account__name', 'account__slug'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'account', 'user', 'role', 'status')
        }),
        ('Permissões', {
            'fields': (
                'can_invite_users', 'can_manage_billing',
                'can_manage_settings', 'can_view_analytics'
            )
        }),
        ('Convite', {
            'fields': ('invited_by', 'invited_at', 'joined_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_memberships', 'deactivate_memberships', 'suspend_memberships']
    
    def activate_memberships(self, request, queryset):
        for membership in queryset:
            membership.activate()
        self.message_user(request, f'{queryset.count()} membros foram ativados.')
    activate_memberships.short_description = 'Ativar membros selecionados'
    
    def deactivate_memberships(self, request, queryset):
        for membership in queryset:
            membership.deactivate()
        self.message_user(request, f'{queryset.count()} membros foram desativados.')
    deactivate_memberships.short_description = 'Desativar membros selecionados'
    
    def suspend_memberships(self, request, queryset):
        for membership in queryset:
            membership.suspend()
        self.message_user(request, f'{queryset.count()} membros foram suspensos.')
    suspend_memberships.short_description = 'Suspender membros selecionados'


@admin.register(AccountInvitation)
class AccountInvitationAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'account', 'role', 'status', 'invited_by',
        'expires_at', 'is_expired_display', 'created_at'
    )
    list_filter = ('role', 'status', 'created_at', 'expires_at')
    search_fields = ('email', 'account__name', 'invited_by__username')
    readonly_fields = ('id', 'token', 'created_at', 'updated_at', 'is_expired_display')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'account', 'email', 'role', 'status')
        }),
        ('Permissões', {
            'fields': (
                'can_invite_users', 'can_manage_billing',
                'can_manage_settings', 'can_view_analytics'
            )
        }),
        ('Convite', {
            'fields': ('invited_by', 'token', 'expires_at', 'accepted_at', 'is_expired_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Sim</span>')
        return format_html('<span style="color: green;">Não</span>')
    is_expired_display.short_description = 'Expirado'
    
    actions = ['cancel_invitations', 'extend_expiration']
    
    def cancel_invitations(self, request, queryset):
        for invitation in queryset:
            invitation.cancel()
        self.message_user(request, f'{queryset.count()} convites foram cancelados.')
    cancel_invitations.short_description = 'Cancelar convites selecionados'
    
    def extend_expiration(self, request, queryset):
        from datetime import timedelta
        for invitation in queryset:
            invitation.expires_at += timedelta(days=7)
            invitation.save()
        self.message_user(request, f'Expiração estendida por 7 dias para {queryset.count()} convites.')
    extend_expiration.short_description = 'Estender expiração por 7 dias'
