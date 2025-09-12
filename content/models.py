from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
import uuid


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ['slug', 'account']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('content:category_detail', kwargs={'slug': self.slug})


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, blank=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['slug', 'account']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Content(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    ]
    
    CONTENT_TYPES = [
        ('article', 'Artigo'),
        ('page', 'Página'),
        ('post', 'Post'),
        ('news', 'Notícia'),
        ('product', 'Produto'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='article')
    excerpt = models.TextField(max_length=500, blank=True, help_text='Resumo do conteúdo')
    content = models.TextField(help_text='Conteúdo principal')
    featured_image = models.ImageField(upload_to='content/images/', blank=True, null=True)
    
    # Relacionamentos
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contents')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    
    # Status e datas
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text='Destacar este conteúdo')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, help_text='Título para SEO (máx. 60 caracteres)')
    meta_description = models.CharField(max_length=160, blank=True, help_text='Descrição para SEO (máx. 160 caracteres)')
    
    # Estatísticas
    views_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['slug', 'account']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['account', 'status']),
            models.Index(fields=['category', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-gerar meta_title se não fornecido
        if not self.meta_title:
            self.meta_title = self.title[:60]
        
        # Auto-gerar meta_description se não fornecido
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('content:content_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class ContentAttachment(models.Model):
    ATTACHMENT_TYPES = [
        ('image', 'Imagem'),
        ('document', 'Documento'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('other', 'Outro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='content/attachments/')
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(help_text='Tamanho do arquivo em bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title or self.file.name
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
