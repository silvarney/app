from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Domain, DomainVerificationLog, DomainConfiguration


class DomainVerificationLogInline(admin.TabularInline):
    model = DomainVerificationLog
    extra = 0
    readonly_fields = ['verification_method', 'status', 'details', 'checked_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class DomainConfigurationInline(admin.StackedInline):
    model = DomainConfiguration
    extra = 0
    fieldsets = [
        ('Cache', {
            'fields': ['cache_enabled', 'cache_ttl']
        }),
        ('SEO', {
            'fields': ['default_title', 'default_description', 'robots_txt']
        }),
        ('Analytics', {
            'fields': ['google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id']
        }),
        ('Segurança', {
            'fields': ['force_https', 'hsts_enabled']
        }),
    ]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'domain_type', 'account', 'status_badge', 
        'is_primary', 'is_active', 'ssl_status', 'verified_at', 'created_at'
    ]
    list_filter = [
        'status', 'domain_type', 'is_primary', 'ssl_enabled', 
        'is_active', 'verification_method', 'created_at'
    ]
    search_fields = ['name', 'account__name']
    readonly_fields = [
        'verification_token', 'verified_at', 'last_checked_at', 
        'created_at', 'updated_at', 'verification_instructions_display'
    ]
    list_editable = ['is_active']
    ordering = ['-is_primary', 'name']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'domain_type', 'account', 'is_active', 'is_primary']
        }),
        ('Verificação', {
            'fields': [
                'status', 'verification_method', 'verification_token',
                'verification_instructions_display', 'verified_at', 'last_checked_at'
            ]
        }),
        ('SSL/TLS', {
            'fields': ['ssl_enabled', 'ssl_certificate', 'ssl_private_key', 'ssl_expires_at'],
            'classes': ['collapse']
        }),
        ('Redirecionamento', {
            'fields': ['redirect_to', 'redirect_type'],
            'classes': ['collapse']
        }),
        ('Datas', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [DomainConfigurationInline, DomainVerificationLogInline]
    
    actions = ['verify_domains', 'mark_as_verified', 'mark_as_pending']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Filtrar por conta do usuário se não for superuser
            if hasattr(request.user, 'account_memberships'):
                user_accounts = request.user.account_memberships.values_list('account_id', flat=True)
                qs = qs.filter(account_id__in=user_accounts)
        return qs.select_related('account').prefetch_related('verification_logs')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'verified': '#10b981',
            'failed': '#ef4444',
            'expired': '#6b7280'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def ssl_status(self, obj):
        if obj.ssl_enabled:
            if obj.check_ssl_expiry():
                return format_html('<span style="color: #ef4444;">🔒 Expirado</span>')
            return format_html('<span style="color: #10b981;">🔒 Ativo</span>')
        return format_html('<span style="color: #6b7280;">🔓 Desabilitado</span>')
    ssl_status.short_description = 'SSL'
    
    def verification_instructions_display(self, obj):
        instructions = obj.verification_instructions
        if instructions:
            return format_html(
                '<strong>Tipo:</strong> {}<br>'
                '<strong>Nome:</strong> <code>{}</code><br>'
                '<strong>Valor:</strong> <code>{}</code><br>'
                '<strong>Instruções:</strong> {}',
                instructions.get('type', ''),
                instructions.get('name', ''),
                instructions.get('value', ''),
                instructions.get('instructions', '')
            )
        return 'Nenhuma instrução disponível'
    verification_instructions_display.short_description = 'Instruções de Verificação'
    
    def verify_domains(self, request, queryset):
        verified_count = 0
        for domain in queryset:
            if domain.verification_method == 'dns_txt':
                if domain.verify_dns_txt():
                    verified_count += 1
            elif domain.verification_method == 'dns_cname':
                if domain.verify_dns_cname():
                    verified_count += 1
        
        self.message_user(
            request,
            f'{verified_count} domínio(s) verificado(s) com sucesso.'
        )
    verify_domains.short_description = 'Verificar domínios selecionados'
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(
            status='verified',
            verified_at=timezone.now(),
            last_checked_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} domínio(s) marcado(s) como verificado(s).'
        )
    mark_as_verified.short_description = 'Marcar como verificado'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(
            request,
            f'{updated} domínio(s) marcado(s) como pendente(s).'
        )
    mark_as_pending.short_description = 'Marcar como pendente'


@admin.register(DomainVerificationLog)
class DomainVerificationLogAdmin(admin.ModelAdmin):
    list_display = ['domain', 'verification_method', 'status', 'checked_at']
    list_filter = ['status', 'verification_method', 'checked_at']
    search_fields = ['domain__name']
    readonly_fields = ['domain', 'verification_method', 'status', 'details', 'checked_at']
    ordering = ['-checked_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DomainConfiguration)
class DomainConfigurationAdmin(admin.ModelAdmin):
    list_display = ['domain', 'cache_enabled', 'force_https', 'hsts_enabled']
    list_filter = ['cache_enabled', 'force_https', 'hsts_enabled']
    search_fields = ['domain__name']
    
    fieldsets = [
        ('Domínio', {
            'fields': ['domain']
        }),
        ('Cache', {
            'fields': ['cache_enabled', 'cache_ttl']
        }),
        ('SEO', {
            'fields': ['default_title', 'default_description', 'robots_txt']
        }),
        ('Analytics', {
            'fields': ['google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id']
        }),
        ('Segurança', {
            'fields': ['force_https', 'hsts_enabled']
        }),
    ]
