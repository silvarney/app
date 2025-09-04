from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import UploadedFile, ImageThumbnail, UploadQuota


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = [
        'original_name', 'account', 'uploaded_by', 'file_type', 
        'file_size_human', 'is_public', 'created_at', 'file_preview'
    ]
    list_filter = [
        'file_type', 'is_public', 'created_at', 'account'
    ]
    search_fields = [
        'original_name', 'description', 'uploaded_by__email', 
        'account__name'
    ]
    readonly_fields = [
        'id', 'file_size', 'mime_type', 'file_type', 'created_at', 
        'updated_at', 'file_preview', 'file_info'
    ]
    fieldsets = [
        ('Arquivo', {
            'fields': ('id', 'file', 'original_name', 'file_preview')
        }),
        ('Metadados', {
            'fields': ('description', 'alt_text', 'is_public')
        }),
        ('Informações Técnicas', {
            'fields': ('file_size', 'mime_type', 'file_type', 'file_info'),
            'classes': ('collapse',)
        }),
        ('Relacionamentos', {
            'fields': ('account', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ]
    
    def file_preview(self, obj):
        """Preview do arquivo"""
        if obj.is_image:
            # Tentar usar thumbnail pequeno
            try:
                thumbnail = obj.thumbnails.filter(size='small').first()
                if thumbnail:
                    return format_html(
                        '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                        reverse('uploads:thumbnail_serve', args=[obj.id, 'small'])
                    )
            except:
                pass
            
            # Fallback para imagem original
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                reverse('uploads:file_serve', args=[obj.id])
            )
        else:
            return format_html(
                '<div style="padding: 10px; background: #f0f0f0; text-align: center;">{}</div>',
                obj.file_type.upper()
            )
    
    file_preview.short_description = 'Preview'
    
    def file_info(self, obj):
        """Informações detalhadas do arquivo"""
        info = [
            f"<strong>ID:</strong> {obj.id}",
            f"<strong>Tamanho:</strong> {obj.file_size_human}",
            f"<strong>MIME Type:</strong> {obj.mime_type}",
            f"<strong>Tipo:</strong> {obj.get_file_type_display()}",
        ]
        
        if obj.is_image:
            info.append(f"<strong>É Imagem:</strong> Sim")
            # Adicionar informações de thumbnails
            thumbnails = obj.thumbnails.all()
            if thumbnails:
                info.append(f"<strong>Thumbnails:</strong> {thumbnails.count()}")
        
        return mark_safe("<br>".join(info))
    
    file_info.short_description = 'Informações do Arquivo'


class ImageThumbnailInline(admin.TabularInline):
    model = ImageThumbnail
    extra = 0
    readonly_fields = ['size', 'width', 'height', 'created_at']
    fields = ['size', 'width', 'height', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ImageThumbnail)
class ImageThumbnailAdmin(admin.ModelAdmin):
    list_display = [
        'original_file', 'size', 'width', 'height', 
        'created_at'
    ]
    list_filter = ['size', 'created_at']
    search_fields = ['original_file__original_name']
    readonly_fields = [
        'original_file', 'size', 'file', 'width', 'height', 
        'created_at'
    ]
    
    def has_add_permission(self, request):
        return False


@admin.register(UploadQuota)
class UploadQuotaAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'used_storage_mb', 'max_storage_mb', 
        'storage_percentage', 'files_uploaded_this_month', 
        'max_files_per_month', 'is_storage_full'
    ]
    list_filter = ['account']
    search_fields = ['account__name']
    readonly_fields = [
        'used_storage_bytes', 'files_uploaded_this_month', 
        'storage_percentage', 'is_storage_full', 
        'is_monthly_limit_reached', 'quota_info'
    ]
    fieldsets = [
        ('Conta', {
            'fields': ('account',)
        }),
        ('Limites', {
            'fields': (
                'max_storage_mb', 'max_file_size_mb', 
                'max_files_per_month'
            )
        }),
        ('Uso Atual', {
            'fields': (
                'used_storage_bytes', 'files_uploaded_this_month', 
                'quota_info'
            ),
            'classes': ('collapse',)
        })
    ]
    
    def storage_percentage(self, obj):
        """Percentual de armazenamento usado"""
        return f"{obj.storage_percentage:.1f}%"
    
    storage_percentage.short_description = 'Uso (%)'
    
    def is_storage_full(self, obj):
        """Indicador se o armazenamento está cheio"""
        if obj.is_storage_full:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔴 Cheio</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">🟢 OK</span>'
            )
    
    is_storage_full.short_description = 'Status'
    
    def quota_info(self, obj):
        """Informações detalhadas da quota"""
        info = [
            f"<strong>Armazenamento:</strong> {obj.used_storage_mb:.2f} MB / {obj.max_storage_mb} MB ({obj.storage_percentage:.1f}%)",
            f"<strong>Arquivos este mês:</strong> {obj.files_uploaded_this_month} / {obj.max_files_per_month}",
        ]
        
        if obj.is_storage_full:
            info.append('<span style="color: red;"><strong>⚠️ Armazenamento cheio!</strong></span>')
        
        if obj.is_monthly_limit_reached:
            info.append('<span style="color: orange;"><strong>⚠️ Limite mensal atingido!</strong></span>')
        
        return mark_safe("<br>".join(info))
    
    quota_info.short_description = 'Informações da Quota'
    
    actions = ['reset_monthly_counter']
    
    def reset_monthly_counter(self, request, queryset):
        """Resetar contador mensal"""
        count = 0
        for quota in queryset:
            quota.reset_monthly_counter()
            count += 1
        
        self.message_user(
            request,
            f"Contador mensal resetado para {count} quota(s)."
        )
    
    reset_monthly_counter.short_description = "Resetar contador mensal"
