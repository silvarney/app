from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
import dns.resolver
import socket
import uuid


class Domain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('verified', 'Verificado'),
        ('failed', 'Falhou'),
        ('expired', 'Expirado'),
    ]
    
    DOMAIN_TYPES = [
        ('primary', 'Principal'),
        ('subdomain', 'Subdomínio'),
        ('custom', 'Personalizado'),
    ]
    
    # Validador para domínio
    domain_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,}$',
        message='Digite um domínio válido (ex: exemplo.com)'
    )
    
    name = models.CharField(
        max_length=255, 
        validators=[domain_validator],
        help_text='Nome do domínio (ex: exemplo.com)'
    )
    domain_type = models.CharField(max_length=20, choices=DOMAIN_TYPES, default='custom')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='domains')
    
    # Status e verificação
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_token = models.CharField(max_length=64, unique=True, blank=True)
    verification_method = models.CharField(
        max_length=20,
        choices=[
            ('dns_txt', 'DNS TXT Record'),
            ('dns_cname', 'DNS CNAME Record'),
            ('file_upload', 'File Upload'),
        ],
        default='dns_txt'
    )
    
    # Configurações SSL
    ssl_enabled = models.BooleanField(default=False)
    ssl_certificate = models.TextField(blank=True, help_text='Certificado SSL')
    ssl_private_key = models.TextField(blank=True, help_text='Chave privada SSL')
    ssl_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Configurações de redirecionamento
    redirect_to = models.URLField(blank=True, help_text='URL para redirecionamento')
    redirect_type = models.CharField(
        max_length=10,
        choices=[
            ('301', 'Permanente (301)'),
            ('302', 'Temporário (302)'),
        ],
        blank=True
    )
    
    # Configurações avançadas
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text='Domínio principal da conta')
    
    # Datas
    verified_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'name']
        unique_together = ['name', 'account']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Gerar token de verificação se não existir
        if not self.verification_token:
            import secrets
            self.verification_token = secrets.token_urlsafe(32)
        
        # Garantir que apenas um domínio seja principal por conta
        if self.is_primary:
            Domain.objects.filter(account=self.account, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def verify_dns_txt(self):
        """Verifica se o registro TXT DNS está configurado corretamente"""
        try:
            txt_records = dns.resolver.resolve(f'_saas-verification.{self.name}', 'TXT')
            for record in txt_records:
                if self.verification_token in str(record):
                    self.status = 'verified'
                    self.verified_at = timezone.now()
                    self.last_checked_at = timezone.now()
                    self.save()
                    return True
        except Exception as e:
            self.status = 'failed'
            self.last_checked_at = timezone.now()
            self.save()
        return False
    
    def verify_dns_cname(self):
        """Verifica se o registro CNAME DNS está configurado corretamente"""
        try:
            cname_records = dns.resolver.resolve(self.name, 'CNAME')
            for record in cname_records:
                if 'saas-platform.com' in str(record):  # Substitua pelo seu domínio
                    self.status = 'verified'
                    self.verified_at = timezone.now()
                    self.last_checked_at = timezone.now()
                    self.save()
                    return True
        except Exception as e:
            self.status = 'failed'
            self.last_checked_at = timezone.now()
            self.save()
        return False
    
    def check_ssl_expiry(self):
        """Verifica se o certificado SSL está próximo do vencimento"""
        if self.ssl_expires_at and self.ssl_expires_at <= timezone.now():
            return True
        return False
    
    @property
    def verification_instructions(self):
        """Retorna instruções de verificação baseadas no método escolhido"""
        if self.verification_method == 'dns_txt':
            return {
                'type': 'TXT',
                'name': f'_saas-verification.{self.name}',
                'value': self.verification_token,
                'instructions': f'Adicione um registro TXT com o nome "_saas-verification.{self.name}" e valor "{self.verification_token}"'
            }
        elif self.verification_method == 'dns_cname':
            return {
                'type': 'CNAME',
                'name': self.name,
                'value': 'saas-platform.com',  # Substitua pelo seu domínio
                'instructions': f'Adicione um registro CNAME apontando "{self.name}" para "saas-platform.com"'
            }
        return {}


class DomainVerificationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='verification_logs')
    verification_method = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    details = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-checked_at']
    
    def __str__(self):
        return f'{self.domain.name} - {self.status} ({self.checked_at})'


class DomainConfiguration(models.Model):
    """Configurações específicas por domínio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.OneToOneField(Domain, on_delete=models.CASCADE, related_name='configuration')
    
    # Configurações de cache
    cache_enabled = models.BooleanField(default=True)
    cache_ttl = models.PositiveIntegerField(default=3600, help_text='TTL do cache em segundos')
    
    # Configurações de SEO
    default_title = models.CharField(max_length=60, blank=True)
    default_description = models.CharField(max_length=160, blank=True)
    robots_txt = models.TextField(blank=True, help_text='Conteúdo do robots.txt')
    
    # Configurações de analytics
    google_analytics_id = models.CharField(max_length=20, blank=True)
    google_tag_manager_id = models.CharField(max_length=20, blank=True)
    facebook_pixel_id = models.CharField(max_length=20, blank=True)
    
    # Configurações de segurança
    force_https = models.BooleanField(default=True)
    hsts_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Config: {self.domain.name}'
