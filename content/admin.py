from django.contrib import admin
from .models import Category, Tag, Content, ContentAttachment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'account', 'is_active', 'created_at']
    list_filter = ['is_active', 'account', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filtrar por contas do usuário
        return qs.filter(account__memberships__user=request.user)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'account', 'created_at']
    list_filter = ['account', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(account__memberships__user=request.user)


class ContentAttachmentInline(admin.TabularInline):
    model = ContentAttachment
    extra = 0
    fields = ['file', 'file_type', 'title', 'description']
    readonly_fields = ['file_size']


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'status', 'author', 'category', 'is_featured', 'views_count', 'published_at', 'created_at']
    list_filter = ['status', 'content_type', 'is_featured', 'category', 'account', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['status', 'is_featured']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    filter_horizontal = ['tags']
    inlines = [ContentAttachmentInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'content_type', 'author', 'account', 'category')
        }),
        ('Conteúdo', {
            'fields': ('excerpt', 'content', 'featured_image', 'tags')
        }),
        ('Status e Publicação', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Estatísticas', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['views_count']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(account__memberships__user=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContentAttachment)
class ContentAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'content', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'description', 'content__title']
    readonly_fields = ['file_size']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(content__account__memberships__user=request.user)
