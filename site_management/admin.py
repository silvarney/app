from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TemplateCategory, PlanType, Item, Site, SiteBio, SocialNetwork,
    Banner, CTA, SiteCategory, Service, BlogPost, Subscription,
    SubscriptionItem, Payment
)


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'description']
        }),
        ('Imagens', {
            'fields': ['desktop_image', 'mobile_image']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    list_display = ['title', 'template_category', 'discount', 'total_value_display', 'final_value_display', 'is_active', 'created_at']
    list_filter = ['template_category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'discount']
    readonly_fields = ['created_at', 'updated_at', 'total_value_display', 'final_value_display']
    filter_horizontal = ['items']
    
    def total_value_display(self, obj):
        return f"R$ {obj.total_value:.2f}"
    total_value_display.short_description = 'Valor Total'
    
    def final_value_display(self, obj):
        return f"R$ {obj.final_value:.2f}"
    final_value_display.short_description = 'Valor Final'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'template_category', 'description')
        }),
        ('Itens e Preços', {
            'fields': ('items', 'discount')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Valores Calculados', {
            'fields': ('total_value_display', 'final_value_display'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'value', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'value')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class SiteBioInline(admin.StackedInline):
    model = SiteBio
    extra = 0
    fields = ['bio_text', 'profile_image']


class SocialNetworkInline(admin.TabularInline):
    model = SocialNetwork
    extra = 0
    fields = ['platform', 'url', 'is_active']


class BannerInline(admin.TabularInline):
    model = Banner
    extra = 0
    fields = ['title', 'image', 'link', 'is_active', 'order']


class CTAInline(admin.TabularInline):
    model = CTA
    extra = 0
    fields = ['title', 'description', 'button_text', 'button_link', 'is_active']


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['domain', 'account', 'plan_type', 'status', 'created_at', 'site_link']
    list_filter = ['status', 'template_category', 'created_at', 'account']
    search_fields = ['domain', 'account__name']
    list_editable = ['status']
    readonly_fields = ['id', 'created_at', 'updated_at', 'site_preview', 'payment_date', 'payment_link', 'contract_date', 'expiration_date']
    autocomplete_fields = ['account']
    inlines = [SiteBioInline, SocialNetworkInline, BannerInline, CTAInline]
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['domain', 'account', 'template_category', 'plan_type']
        }),
        ('Status e Configurações', {
            'fields': ['status']
        }),
        ('Informações de Pagamento', {
            'fields': ['payment_date', 'payment_link', 'contract_date', 'expiration_date'],
            'classes': ['collapse']
        }),
        ('Preview', {
            'fields': ['site_preview'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def site_link(self, obj):
        if obj.domain:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.domain, obj.domain)
        return '-'
    site_link.short_description = 'Link do Site'
    
    def site_preview(self, obj):
        if obj.plan_type and obj.plan_type.template_category and obj.plan_type.template_category.desktop_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px;" />',
                obj.plan_type.template_category.desktop_image.url
            )
        return 'Sem preview disponível'
    site_preview.short_description = 'Preview do Template'


@admin.register(SiteCategory)
class SiteCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'site', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'site__account']
    search_fields = ['name', 'description', 'site__domain']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['site']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'description', 'site']
        }),
        ('Configurações', {
            'fields': ['is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'site', 'value', 'final_value_display', 'is_active', 'order']
    list_filter = ['is_active', 'site', 'category', 'created_at']
    search_fields = ['title', 'description', 'site__domain']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at', 'final_value_display']
    autocomplete_fields = ['site', 'category']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['title', 'description', 'site', 'category']
        }),
        ('Preços', {
            'fields': ['value', 'discount', 'final_value_display']
        }),
        ('Configurações', {
            'fields': ['is_active', 'order', 'image']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def final_value_display(self, obj):
        """Exibe o valor final com desconto aplicado"""
        return f"R$ {obj.final_value:.2f}" if obj.final_value else "-"
    final_value_display.short_description = "Valor Final"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'site', 'is_published', 'published_at', 'created_at']
    list_filter = ['is_published', 'published_at', 'site', 'category', 'created_at']
    search_fields = ['title', 'content', 'site__domain']
    list_editable = ['is_published']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['site', 'category']
    date_hierarchy = 'published_at'
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['title', 'slug', 'site', 'category']
        }),
        ('Conteúdo', {
            'fields': ['content', 'featured_image']
        }),
        ('Publicação', {
            'fields': ['is_published', 'published_at']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


class SubscriptionItemInline(admin.TabularInline):
    model = SubscriptionItem
    extra = 0
    fields = ['item', 'title', 'description', 'value']
    readonly_fields = ['value']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['title', 'total_value', 'status', 'payment_month', 'payment_year']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['site', 'account', 'status', 'created_at', 'total_value_display']
    list_filter = ['status', 'created_at', 'account']
    search_fields = ['site__domain', 'account__name']
    readonly_fields = ['created_at', 'updated_at', 'total_value_display']
    autocomplete_fields = ['site', 'account']
    inlines = [SubscriptionItemInline, PaymentInline]
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['site', 'account', 'status']
        }),
        ('Valores', {
            'fields': ['total_value_display']
        }),
        ('Datas', {
            'fields': ['created_at', 'updated_at', 'expires_at']
        })
    ]
    
    def total_value_display(self, obj):
        return f'R$ {obj.total_value():.2f}'
    total_value_display.short_description = 'Valor Total'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'title', 'total_value', 'status', 'payment_month', 'payment_year']
    list_filter = ['status', 'payment_year', 'created_at']
    search_fields = ['subscription__site__domain', 'subscription__account__email', 'title']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['subscription']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['subscription', 'amount', 'payment_method']
        }),
        ('Status', {
            'fields': ['status', 'paid_at']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
