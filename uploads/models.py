import os
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from accounts.models import Account

User = get_user_model()


def upload_to(instance, filename):
    """Função para definir o caminho de upload dos arquivos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', str(instance.account.id), filename)


class UploadedFile(models.Model):
    """Modelo para arquivos enviados pelos usuários"""
    
    FILE_TYPE_CHOICES = [
        ('image', 'Imagem'),
        ('document', 'Documento'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('other', 'Outro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    
    # Arquivo
    file = models.FileField(upload_to=upload_to)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField()  # em bytes
    mime_type = models.CharField(max_length=100)
    
    # Metadados para imagens
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    
    # Informações adicionais
    description = models.TextField(blank=True)
    alt_text = models.CharField(max_length=255, blank=True)  # Para acessibilidade
    
    # Controle
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'uploads_file'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'file_type']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_name} ({self.account.name})"
    
    def save(self, *args, **kwargs):
        if self.file:
            # Definir nome original se não estiver definido
            if not self.original_name:
                self.original_name = self.file.name
            
            # Definir tamanho do arquivo
            if not self.file_size:
                self.file_size = self.file.size
            
            # Detectar tipo de arquivo
            if not self.file_type:
                self.file_type = self._detect_file_type()
            
            # Para imagens, extrair dimensões
            if self.file_type == 'image' and not self.width:
                try:
                    image = Image.open(self.file)
                    self.width, self.height = image.size
                except Exception:
                    pass
        
        super().save(*args, **kwargs)
    
    def _detect_file_type(self):
        """Detecta o tipo de arquivo baseado na extensão"""
        if not self.file:
            return 'other'
        
        ext = self.file.name.lower().split('.')[-1]
        
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        document_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
        video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
        audio_extensions = ['mp3', 'wav', 'ogg', 'aac', 'flac']
        
        if ext in image_extensions:
            return 'image'
        elif ext in document_extensions:
            return 'document'
        elif ext in video_extensions:
            return 'video'
        elif ext in audio_extensions:
            return 'audio'
        else:
            return 'other'
    
    @property
    def file_size_human(self):
        """Retorna o tamanho do arquivo em formato legível"""
        if not self.file_size:
            return '0 B'
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def is_image(self):
        """Verifica se o arquivo é uma imagem"""
        return self.file_type == 'image'
    
    def get_thumbnail_url(self, size='medium'):
        """Retorna URL do thumbnail (se for imagem)"""
        if not self.is_image:
            return None
        
        # Aqui você implementaria a lógica de thumbnail
        # Por enquanto, retorna a URL original
        return self.file.url if self.file else None


class ImageThumbnail(models.Model):
    """Modelo para thumbnails de imagens"""
    
    SIZE_CHOICES = [
        ('small', 'Pequeno (150x150)'),
        ('medium', 'Médio (300x300)'),
        ('large', 'Grande (600x600)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='thumbnails')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    
    # Arquivo thumbnail
    file = models.ImageField(upload_to='thumbnails/')
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'uploads_thumbnail'
        unique_together = ['original_file', 'size']
        indexes = [
            models.Index(fields=['original_file', 'size']),
        ]
    
    def __str__(self):
        return f"Thumbnail {self.size} - {self.original_file.original_name}"
    
    @classmethod
    def create_thumbnail(cls, uploaded_file, size='medium'):
        """Cria um thumbnail para uma imagem"""
        if not uploaded_file.is_image:
            return None
        
        # Definir dimensões baseado no tamanho
        size_map = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600),
        }
        
        target_size = size_map.get(size, (300, 300))
        
        try:
            # Abrir imagem original
            image = Image.open(uploaded_file.file)
            
            # Converter para RGB se necessário
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Redimensionar mantendo proporção
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Salvar thumbnail
            thumb_io = BytesIO()
            image.save(thumb_io, format='JPEG', quality=85)
            thumb_io.seek(0)
            
            # Criar nome do arquivo
            original_name = uploaded_file.original_name
            name_without_ext = os.path.splitext(original_name)[0]
            thumb_name = f"{name_without_ext}_{size}.jpg"
            
            # Criar objeto thumbnail
            thumbnail = cls(
                original_file=uploaded_file,
                size=size,
                width=image.width,
                height=image.height
            )
            
            thumbnail.file.save(
                thumb_name,
                ContentFile(thumb_io.getvalue()),
                save=False
            )
            
            thumbnail.save()
            return thumbnail
            
        except Exception as e:
            print(f"Erro ao criar thumbnail: {e}")
            return None


class UploadQuota(models.Model):
    """Modelo para controle de quota de upload por conta"""
    
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='upload_quota')
    
    # Limites
    max_storage_mb = models.PositiveIntegerField(default=1000)  # 1GB padrão
    max_file_size_mb = models.PositiveIntegerField(default=10)  # 10MB por arquivo
    max_files_per_month = models.PositiveIntegerField(default=100)
    
    # Uso atual
    used_storage_bytes = models.BigIntegerField(default=0)
    files_uploaded_this_month = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'uploads_quota'
    
    def __str__(self):
        return f"Quota - {self.account.name}"
    
    @property
    def used_storage_mb(self):
        """Retorna o armazenamento usado em MB"""
        return self.used_storage_bytes / (1024 * 1024)
    
    @property
    def storage_percentage(self):
        """Retorna a porcentagem de armazenamento usado"""
        if self.max_storage_mb == 0:
            return 0
        return (self.used_storage_mb / self.max_storage_mb) * 100
    
    @property
    def is_storage_full(self):
        """Verifica se o armazenamento está cheio"""
        return self.used_storage_mb >= self.max_storage_mb
    
    @property
    def is_monthly_limit_reached(self):
        """Verifica se o limite mensal foi atingido"""
        return self.files_uploaded_this_month >= self.max_files_per_month
    
    def can_upload_file(self, file_size_bytes):
        """Verifica se um arquivo pode ser enviado"""
        # Verificar limite mensal
        if self.is_monthly_limit_reached:
            return False, "Limite mensal de arquivos atingido"
        
        # Verificar tamanho do arquivo
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"Arquivo muito grande. Máximo: {self.max_file_size_mb}MB"
        
        # Verificar espaço disponível
        if (self.used_storage_bytes + file_size_bytes) > (self.max_storage_mb * 1024 * 1024):
            return False, "Espaço de armazenamento insuficiente"
        
        return True, "OK"
    
    def add_file_usage(self, file_size_bytes):
        """Adiciona uso de arquivo à quota"""
        self.used_storage_bytes += file_size_bytes
        self.files_uploaded_this_month += 1
        self.save()
    
    def remove_file_usage(self, file_size_bytes):
        """Remove uso de arquivo da quota"""
        self.used_storage_bytes = max(0, self.used_storage_bytes - file_size_bytes)
        self.save()
    
    def reset_monthly_counter(self):
        """Reseta o contador mensal"""
        today = timezone.now().date()
        if today.month != self.last_reset_date.month or today.year != self.last_reset_date.year:
            self.files_uploaded_this_month = 0
            self.last_reset_date = today
            self.save()
