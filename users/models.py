from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os


class User(AbstractUser):
    """Modelo de usuário customizado com campos adicionais"""
    
    STATUS_CHOICES = [
        ('active', _('Ativo')),
        ('inactive', _('Inativo')),
        ('pending', _('Pendente')),
        ('suspended', _('Suspenso')),
    ]
    
    USER_TYPE_CHOICES = [
        ('user', _('Usuário Comum')),
        ('admin', _('Administrador')),
        ('superadmin', _('Super Administrador')),
    ]
    
    email = models.EmailField(_('Email'), unique=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(
        _('Avatar'), 
        upload_to='avatars/', 
        blank=True, 
        null=True,
        help_text=_('Imagem de perfil do usuário')
    )
    status = models.CharField(
        _('Status'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    user_type = models.CharField(
        _('Tipo de Usuário'), 
        max_length=20, 
        choices=USER_TYPE_CHOICES, 
        default='user'
    )
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(
        _('Último IP de login'), 
        blank=True, 
        null=True
    )
    email_verified = models.BooleanField(_('Email verificado'), default=False)
    phone_verified = models.BooleanField(_('Telefone verificado'), default=False)
    
    # Campos para controle de tentativas de login
    failed_login_attempts = models.PositiveIntegerField(
        _('Tentativas de login falhadas'), 
        default=0
    )
    locked_until = models.DateTimeField(
        _('Bloqueado até'), 
        blank=True, 
        null=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_short_name(self):
        """Retorna o primeiro nome do usuário"""
        return self.first_name or self.username
    
    def save(self, *args, **kwargs):
        """Override do save para redimensionar avatar"""
        super().save(*args, **kwargs)
        
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)
    
    def delete(self, *args, **kwargs):
        """Override do delete para remover arquivo de avatar"""
        if self.avatar:
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)
    
    @property
    def is_active_user(self):
        """Verifica se o usuário está ativo"""
        return self.status == 'active' and self.is_active
    
    @property
    def is_locked(self):
        """Verifica se o usuário está bloqueado"""
        from django.utils import timezone
        return self.locked_until and self.locked_until > timezone.now()
    
    def reset_failed_attempts(self):
        """Reseta as tentativas de login falhadas"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def increment_failed_attempts(self):
        """Incrementa as tentativas de login falhadas"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        
        # Bloqueia por 30 minutos após 5 tentativas
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


class UserProfile(models.Model):
    """Perfil estendido do usuário com informações adicionais"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name=_('Usuário')
    )
    bio = models.TextField(_('Biografia'), max_length=500, blank=True)
    birth_date = models.DateField(_('Data de nascimento'), blank=True, null=True)
    website = models.URLField(_('Website'), blank=True)
    company = models.CharField(_('Empresa'), max_length=100, blank=True)
    job_title = models.CharField(_('Cargo'), max_length=100, blank=True)
    location = models.CharField(_('Localização'), max_length=100, blank=True)
    timezone = models.CharField(
        _('Fuso horário'), 
        max_length=50, 
        default='America/Sao_Paulo'
    )
    language = models.CharField(
        _('Idioma'), 
        max_length=10, 
        default='pt-br'
    )
    
    # Preferências de notificação
    email_notifications = models.BooleanField(
        _('Notificações por email'), 
        default=True
    )
    sms_notifications = models.BooleanField(
        _('Notificações por SMS'), 
        default=False
    )
    push_notifications = models.BooleanField(
        _('Notificações push'), 
        default=True
    )
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Perfil do usuário')
        verbose_name_plural = _('Perfis dos usuários')
    
    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"
