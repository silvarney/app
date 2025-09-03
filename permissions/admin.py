from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import TextInput, Textarea
from .models import Permission, Role, RolePermission, UserRole, UserPermission


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('permission', 'is_active', 'conditions')
    
    formfield_overrides = {
        models.JSONField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('user', 'account', 'status', 'valid_from', 'valid_until', 'assigned_by')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'codename', 'permission_type', 'resource', 'category',
        'is_active', 'created_at'
    )
    list_filter = ('permission_type', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'codename', 'resource', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'codename', 'description')
        }),
        ('Configurações', {
            'fields': ('permission_type', 'resource', 'category', 'content_type')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_permissions', 'deactivate_permissions']
    
    def activate_permissions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} permissões foram ativadas.')
    activate_permissions.short_description = 'Ativar permissões selecionadas'
    
    def deactivate_permissions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} permissões foram desativadas.')
    deactivate_permissions.short_description = 'Desativar permissões selecionadas'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'codename', 'role_type', 'account', 'priority',
        'is_active', 'is_system', 'created_at'
    )
    list_filter = ('role_type', 'is_active', 'is_system', 'priority', 'created_at')
    search_fields = ('name', 'codename', 'description', 'account__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'codename', 'description')
        }),
        ('Configurações', {
            'fields': ('role_type', 'account', 'parent_role', 'priority')
        }),
        ('Status', {
            'fields': ('is_active', 'is_system')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [RolePermissionInline, UserRoleInline]
    
    actions = ['activate_roles', 'deactivate_roles']
    
    def activate_roles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} funções foram ativadas.')
    activate_roles.short_description = 'Ativar funções selecionadas'
    
    def deactivate_roles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} funções foram desativadas.')
    deactivate_roles.short_description = 'Desativar funções selecionadas'


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'role__role_type')
    search_fields = ('role__name', 'permission__name', 'permission__codename')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'role', 'permission')
        }),
        ('Configurações', {
            'fields': ('is_active', 'conditions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    formfield_overrides = {
        models.JSONField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }
    
    actions = ['activate_role_permissions', 'deactivate_role_permissions']
    
    def activate_role_permissions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} permissões de função foram ativadas.')
    activate_role_permissions.short_description = 'Ativar permissões selecionadas'
    
    def deactivate_role_permissions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} permissões de função foram desativadas.')
    deactivate_role_permissions.short_description = 'Desativar permissões selecionadas'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'role', 'account', 'status', 'is_active_display',
        'valid_from', 'valid_until', 'created_at'
    )
    list_filter = ('status', 'role__role_type', 'created_at', 'valid_from', 'valid_until')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'role__name', 'account__name'
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'is_active_display')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user', 'role', 'account')
        }),
        ('Status e Validade', {
            'fields': ('status', 'valid_from', 'valid_until', 'is_active_display')
        }),
        ('Atribuição', {
            'fields': ('assigned_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">Ativo</span>')
        return format_html('<span style="color: red;">Inativo</span>')
    is_active_display.short_description = 'Status Atual'
    
    actions = ['activate_user_roles', 'deactivate_user_roles', 'suspend_user_roles']
    
    def activate_user_roles(self, request, queryset):
        for user_role in queryset:
            user_role.activate()
        self.message_user(request, f'{queryset.count()} funções de usuário foram ativadas.')
    activate_user_roles.short_description = 'Ativar funções selecionadas'
    
    def deactivate_user_roles(self, request, queryset):
        for user_role in queryset:
            user_role.deactivate()
        self.message_user(request, f'{queryset.count()} funções de usuário foram desativadas.')
    deactivate_user_roles.short_description = 'Desativar funções selecionadas'
    
    def suspend_user_roles(self, request, queryset):
        for user_role in queryset:
            user_role.suspend()
        self.message_user(request, f'{queryset.count()} funções de usuário foram suspensas.')
    suspend_user_roles.short_description = 'Suspender funções selecionadas'


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'permission', 'account', 'grant_type', 'is_valid_display',
        'valid_from', 'valid_until', 'created_at'
    )
    list_filter = ('grant_type', 'is_active', 'created_at', 'valid_from', 'valid_until')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'permission__name', 'account__name'
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'is_valid_display')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'user', 'permission', 'account')
        }),
        ('Concessão', {
            'fields': ('grant_type', 'is_active')
        }),
        ('Objeto Específico', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Condições e Validade', {
            'fields': ('conditions', 'valid_from', 'valid_until', 'is_valid_display')
        }),
        ('Concessão', {
            'fields': ('granted_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    formfield_overrides = {
        models.JSONField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }
    
    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">Válido</span>')
        return format_html('<span style="color: red;">Inválido</span>')
    is_valid_display.short_description = 'Status de Validade'
    
    actions = ['activate_user_permissions', 'deactivate_user_permissions']
    
    def activate_user_permissions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} permissões de usuário foram ativadas.')
    activate_user_permissions.short_description = 'Ativar permissões selecionadas'
    
    def deactivate_user_permissions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} permissões de usuário foram desativadas.')
    deactivate_user_permissions.short_description = 'Desativar permissões selecionadas'
