from django.contrib import admin
from .models import GlobalSetting, AccountSetting, UserSetting, SettingTemplate


@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'category', 'is_public', 'is_editable', 'created_at']
    list_filter = ['setting_type', 'category', 'is_public', 'is_editable', 'created_at']
    search_fields = ['key', 'description', 'category']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('key', 'value', 'setting_type', 'description')
        }),
        ('Categorização', {
            'fields': ('category',)
        }),
        ('Permissões', {
            'fields': ('is_public', 'is_editable')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and not obj.is_editable:
            readonly.extend(['key', 'value', 'setting_type'])
        return readonly


@admin.register(AccountSetting)
class AccountSettingAdmin(admin.ModelAdmin):
    list_display = ['account', 'key', 'value', 'setting_type', 'category', 'is_inherited', 'created_at']
    list_filter = ['setting_type', 'category', 'is_inherited', 'created_at', 'account']
    search_fields = ['key', 'description', 'category', 'account__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['account']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('account', 'key', 'value', 'setting_type', 'description')
        }),
        ('Categorização', {
            'fields': ('category', 'is_inherited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'value', 'setting_type', 'category', 'is_inherited', 'created_at']
    list_filter = ['setting_type', 'category', 'is_inherited', 'created_at']
    search_fields = ['key', 'description', 'category', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'key', 'value', 'setting_type', 'description')
        }),
        ('Categorização', {
            'fields': ('category', 'is_inherited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SettingTemplate)
class SettingTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'setting_type', 'scope', 'category', 'is_required', 'is_public', 'created_at']
    list_filter = ['setting_type', 'scope', 'category', 'is_required', 'is_public', 'created_at']
    search_fields = ['name', 'key', 'description', 'category']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('key', 'name', 'description', 'setting_type', 'default_value')
        }),
        ('Categorização e Escopo', {
            'fields': ('category', 'scope')
        }),
        ('Configurações', {
            'fields': ('is_required', 'is_public', 'validation_rules')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Adiciona help text para validation_rules
        if 'validation_rules' in form.base_fields:
            form.base_fields['validation_rules'].help_text = (
                'Regras de validação em formato JSON. Exemplo: '
                '{"min_length": 5, "max_length": 100, "pattern": "^[a-zA-Z]+$"}'
            )
        return form
