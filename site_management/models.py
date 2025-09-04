from django.db import models
from django.utils import timezone
from accounts.models import Account
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import uuid


class TemplateCategory(models.Model):
    """Categorias de layout para templates"""
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    desktop_image = models.ImageField(upload_to='templates/desktop/', verbose_name='Imagem Desktop')
    mobile_image = models.ImageField(upload_to='templates/mobile/', verbose_name='Imagem Mobile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria de Template'
        verbose_name_plural = 'Categorias de Templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Item(models.Model):
    """Itens que podem ser incluídos em planos"""
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['title']
    
    def __str__(self):
        return self.title


class PlanType(models.Model):
    """Tipos de Planos"""
    title = models.CharField(max_length=200, verbose_name='Título')
    items = models.ManyToManyField(Item, verbose_name='Itens')
    description = models.TextField(verbose_name='Descrição')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Desconto (%)')
    template_category = models.ForeignKey(TemplateCategory, on_delete=models.CASCADE, verbose_name='Template')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de Plano'
        verbose_name_plural = 'Tipos de Planos'
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    @property
    def total_value(self):
        """Soma do preço de todos os itens"""
        return sum(item.value for item in self.items.all())
    
    @property
    def final_value(self):
        """Valor total com desconto aplicado"""
        total = self.total_value
        if self.discount > 0:
            total = total - (total * self.discount / 100)
        return total


class Site(models.Model):
    """Sites das contas"""
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('expired', 'Expirado'),
        ('suspended', 'Suspenso'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sites', verbose_name='Conta')
    domain = models.CharField(max_length=255, unique=True, verbose_name='Domínio')
    template_category = models.ForeignKey(TemplateCategory, on_delete=models.PROTECT, verbose_name='Template')
    plan_type = models.ForeignKey(PlanType, on_delete=models.PROTECT, verbose_name='Plano')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Status')
    
    # Campos automáticos
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='Data de Pagamento')
    payment_link = models.CharField(max_length=500, blank=True, verbose_name='Link de Pagamento')
    contract_date = models.DateTimeField(auto_now_add=True, verbose_name='Data de Contratação')
    expiration_date = models.DateTimeField(verbose_name='Data de Expiração')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.domain} - {self.account.name}"
    
    def clean(self):
        # Validar domínio
        if not self.domain.startswith(('http://', 'https://')):
            self.domain = f"https://{self.domain}"
        
        validator = URLValidator()
        try:
            validator(self.domain)
        except ValidationError:
            raise ValidationError({'domain': 'Domínio inválido'})
    
    def save(self, *args, **kwargs):
        if not self.pk:
            # Gerar link de pagamento único
            self.payment_link = f"https://payment.example.com/{uuid.uuid4()}"
            # Definir data de expiração (30 dias a partir da contratação)
            from datetime import timedelta
            self.expiration_date = timezone.now() + timedelta(days=30)
        
        self.clean()
        super().save(*args, **kwargs)


class SiteBio(models.Model):
    """Informações biográficas do site"""
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='bio', verbose_name='Site')
    title = models.CharField(max_length=200, verbose_name='Título do Site')
    description = models.TextField(blank=True, verbose_name='Descrição')
    favicon = models.ImageField(upload_to='sites/favicons/', blank=True, verbose_name='Favicon')
    logo = models.ImageField(upload_to='sites/logos/', verbose_name='Logo')
    share_image = models.ImageField(upload_to='sites/share/', blank=True, verbose_name='Imagem de Compartilhamento')
    email = models.EmailField(blank=True, verbose_name='Email')
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name='WhatsApp')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    address = models.TextField(blank=True, verbose_name='Endereço')
    google_maps = models.URLField(blank=True, verbose_name='Google Maps')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bio do Site'
        verbose_name_plural = 'Bios dos Sites'
    
    def __str__(self):
        return f"Bio - {self.site.domain}"


class SocialNetwork(models.Model):
    """Redes sociais do site"""
    NETWORK_TYPES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('telegram', 'Telegram'),
        ('web', 'Web'),
    ]
    
    ICON_STYLES = [
        ('outline', 'Contorno'),
        ('filled', 'Preenchido'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='social_networks', verbose_name='Site')
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPES, verbose_name='Tipo')
    url = models.URLField(verbose_name='URL')
    icon_style = models.CharField(max_length=10, choices=ICON_STYLES, default='outline', verbose_name='Estilo do Ícone')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rede Social'
        verbose_name_plural = 'Redes Sociais'
        unique_together = ['site', 'network_type']
    
    def __str__(self):
        return f"{self.get_network_type_display()} - {self.site.domain}"


class Banner(models.Model):
    """Banners do site"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='banners', verbose_name='Site')
    image = models.ImageField(upload_to='sites/banners/', verbose_name='Imagem')
    link = models.URLField(blank=True, verbose_name='Link')
    description = models.TextField(blank=True, verbose_name='Descrição')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"Banner {self.order} - {self.site.domain}"


class CTA(models.Model):
    """Call to Action do site"""
    ACTION_TYPES = [
        ('whatsapp', 'Abrir WhatsApp'),
        ('contact_form', 'Preencher formulário de contato'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='ctas', verbose_name='Site')
    image = models.ImageField(upload_to='sites/ctas/', blank=True, verbose_name='Imagem')
    title = models.CharField(max_length=200, blank=True, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='Ação do Botão')
    button_text = models.CharField(max_length=100, verbose_name='Texto do Botão')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'CTA'
        verbose_name_plural = 'CTAs'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"CTA - {self.title or 'Sem título'} - {self.site.domain}"


class SiteCategory(models.Model):
    """Categorias de serviços do site"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='categories', verbose_name='Site')
    name = models.CharField(max_length=100, verbose_name='Nome')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Ícone')
    image = models.ImageField(upload_to='sites/categories/', blank=True, verbose_name='Imagem')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria do Site'
        verbose_name_plural = 'Categorias dos Sites'
        ordering = ['order', 'name']
        unique_together = ['site', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.site.domain}"


class Service(models.Model):
    """Serviços do site"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='services', verbose_name='Site')
    category = models.ForeignKey(SiteCategory, on_delete=models.CASCADE, related_name='services', verbose_name='Categoria')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    image = models.ImageField(upload_to='sites/services/', blank=True, verbose_name='Imagem')
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Valor')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Desconto (%)')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.site.domain}"
    
    @property
    def final_value(self):
        """Valor com desconto aplicado"""
        if self.value and self.discount > 0:
            return self.value - (self.value * self.discount / 100)
        return self.value


class BlogPost(models.Model):
    """Posts do blog do site"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='blog_posts', verbose_name='Site')
    title = models.CharField(max_length=200, blank=True, verbose_name='Título')
    image = models.ImageField(upload_to='sites/blog/', blank=True, verbose_name='Imagem')
    video_url = models.URLField(blank=True, verbose_name='URL do Vídeo')
    content = models.TextField(blank=True, verbose_name='Texto')
    link = models.URLField(blank=True, verbose_name='Link')
    category = models.ForeignKey(SiteCategory, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Categoria')
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags', help_text='Separar por vírgulas')
    is_published = models.BooleanField(default=False, verbose_name='Publicado')
    published_at = models.DateTimeField(blank=True, null=True, verbose_name='Data de Publicação')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Post do Blog'
        verbose_name_plural = 'Posts do Blog'
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return f"{self.title or 'Sem título'} - {self.site.domain}"
    
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        elif not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """Assinaturas dos sites"""
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('inactive', 'Inativa'),
        ('expired', 'Expirada'),
        ('canceled', 'Cancelada'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='subscriptions', verbose_name='Site')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='site_subscriptions', verbose_name='Conta')
    plan_type = models.ForeignKey(PlanType, on_delete=models.PROTECT, verbose_name='Plano Selecionado')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Desconto (%)')
    payment_link = models.CharField(max_length=500, blank=True, verbose_name='Link de Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Status')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Assinatura {self.plan_type.title} - {self.site.domain}"
    
    @property
    def total_value(self):
        """Valor total a ser pago"""
        total = sum(item.value for item in self.subscription_items.all())
        if self.discount > 0:
            total = total - (total * self.discount / 100)
        return total


class SubscriptionItem(models.Model):
    """Itens da assinatura"""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='subscription_items', verbose_name='Assinatura')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Item')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor do Item')
    title = models.CharField(max_length=200, verbose_name='Título do Item')
    description = models.TextField(verbose_name='Descrição do Item')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Item da Assinatura'
        verbose_name_plural = 'Itens da Assinatura'
        unique_together = ['subscription', 'item']
    
    def __str__(self):
        return f"{self.title} - {self.subscription}"


class Payment(models.Model):
    """Pagamentos das assinaturas"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('canceled', 'Cancelado'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments', verbose_name='Assinatura')
    title = models.CharField(max_length=200, verbose_name='Título')
    items_list = models.TextField(verbose_name='Lista dos Itens')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Desconto')
    total_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Total')
    payment_month = models.PositiveIntegerField(verbose_name='Mês do Pagamento')
    payment_year = models.PositiveIntegerField(verbose_name='Ano do Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-payment_year', '-payment_month']
        unique_together = ['subscription', 'payment_month', 'payment_year']
    
    def __str__(self):
        return f"Pagamento {self.payment_month}/{self.payment_year} - {self.subscription.site.domain}"
