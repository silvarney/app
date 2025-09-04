from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class Account(models.Model):
    """Modelo para contas/organizações no sistema multi-tenant"""
    
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Empresarial'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('suspended', 'Suspenso'),
        ('cancelled', 'Cancelado'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome da Conta', max_length=100)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    
    # Informações da empresa
    email = models.EmailField('E-mail', blank=True)
    company_name = models.CharField('Nome da Empresa', max_length=200, blank=True)
    cnpj = models.CharField(
        'CNPJ', 
        max_length=18, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
            message='Digite um CNPJ válido (XX.XXX.XXX/XXXX-XX)'
        )]
    )
    cpf = models.CharField(
        'CPF', 
        max_length=14, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
            message='Digite um CPF válido (XXX.XXX.XXX-XX)'
        )]
    )
    website = models.URLField('Website', blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    
    # Endereço
    address_line1 = models.CharField('Endereço', max_length=255, blank=True)
    address_line2 = models.CharField('Complemento', max_length=255, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    state = models.CharField('Estado', max_length=100, blank=True)
    postal_code = models.CharField('CEP', max_length=10, blank=True)
    country = models.CharField('País', max_length=100, default='Brasil')
    
    # Plano e status
    plan = models.CharField('Plano', max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Limites do plano
    max_users = models.PositiveIntegerField('Máximo de Usuários', default=5)
    max_storage_gb = models.PositiveIntegerField('Armazenamento (GB)', default=1)
    max_domains = models.PositiveIntegerField('Máximo de Domínios', default=1)
    
    # Configurações
    timezone = models.CharField('Fuso Horário', max_length=50, default='America/Sao_Paulo')
    language = models.CharField('Idioma', max_length=10, default='pt-br')
    
    # Datas importantes
    trial_ends_at = models.DateTimeField('Trial Termina em', null=True, blank=True)
    subscription_ends_at = models.DateTimeField('Assinatura Termina em', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    # Proprietário da conta
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_accounts',
        verbose_name='Proprietário'
    )
    
    class Meta:
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['plan']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_active(self):
        """Verifica se a conta está ativa"""
        return self.status == 'active'
    
    @property
    def is_trial(self):
        """Verifica se a conta está em trial"""
        return self.status == 'trial'
    
    @property
    def trial_expired(self):
        """Verifica se o trial expirou"""
        if self.trial_ends_at:
            return timezone.now() > self.trial_ends_at
        return False
    
    @property
    def subscription_expired(self):
        """Verifica se a assinatura expirou"""
        if self.subscription_ends_at:
            return timezone.now() > self.subscription_ends_at
        return False
    
    @property
    def current_users_count(self):
        """Conta o número atual de usuários"""
        return self.memberships.filter(status='active').count()
    
    @property
    def can_add_users(self):
        """Verifica se pode adicionar mais usuários"""
        return self.current_users_count < self.max_users
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('accounts:detail', kwargs={'slug': self.slug})


class AccountMembership(models.Model):
    """Modelo para membros de uma conta"""
    
    ROLE_CHOICES = [
        ('owner', 'Proprietário'),
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('member', 'Membro'),
        ('viewer', 'Visualizador'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('pending', 'Pendente'),
        ('suspended', 'Suspenso'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Conta'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Usuário'
    )
    
    role = models.CharField('Função', max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Permissões específicas
    can_invite_users = models.BooleanField('Pode Convidar Usuários', default=False)
    can_manage_billing = models.BooleanField('Pode Gerenciar Cobrança', default=False)
    can_manage_settings = models.BooleanField('Pode Gerenciar Configurações', default=False)
    can_view_analytics = models.BooleanField('Pode Ver Análises', default=True)
    
    # Convite
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations',
        verbose_name='Convidado por'
    )
    invited_at = models.DateTimeField('Convidado em', null=True, blank=True)
    joined_at = models.DateTimeField('Entrou em', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Membro da Conta'
        verbose_name_plural = 'Membros da Conta'
        unique_together = ['account', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} - {self.account.name}'
    
    @property
    def is_owner(self):
        """Verifica se é proprietário da conta"""
        return self.role == 'owner'
    
    @property
    def is_admin(self):
        """Verifica se é administrador"""
        return self.role in ['owner', 'admin']
    
    @property
    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.is_admin or self.can_invite_users
    
    def activate(self):
        """Ativa o membro"""
        self.status = 'active'
        if not self.joined_at:
            self.joined_at = timezone.now()
        self.save()
    
    def deactivate(self):
        """Desativa o membro"""
        self.status = 'inactive'
        self.save()
    
    def suspend(self):
        """Suspende o membro"""
        self.status = 'suspended'
        self.save()


class AccountInvitation(models.Model):
    """Modelo para convites de conta"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('accepted', 'Aceito'),
        ('declined', 'Recusado'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='Conta'
    )
    
    # Informações do convite
    email = models.EmailField('E-mail')
    role = models.CharField('Função', max_length=20, choices=AccountMembership.ROLE_CHOICES, default='member')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Permissões específicas
    can_invite_users = models.BooleanField('Pode Convidar Usuários', default=False)
    can_manage_billing = models.BooleanField('Pode Gerenciar Cobrança', default=False)
    can_manage_settings = models.BooleanField('Pode Gerenciar Configurações', default=False)
    can_view_analytics = models.BooleanField('Pode Ver Análises', default=True)
    
    # Quem convidou
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_account_invitations',
        verbose_name='Convidado por'
    )
    
    # Token para aceitar convite
    token = models.CharField('Token', max_length=100, unique=True)
    
    # Datas
    expires_at = models.DateTimeField('Expira em')
    accepted_at = models.DateTimeField('Aceito em', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Convite de Conta'
        verbose_name_plural = 'Convites de Conta'
        unique_together = ['account', 'email']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f'Convite para {self.email} - {self.account.name}'
    
    @property
    def is_expired(self):
        """Verifica se o convite expirou"""
        return timezone.now() > self.expires_at
    
    @property
    def is_pending(self):
        """Verifica se o convite está pendente"""
        return self.status == 'pending' and not self.is_expired
    
    def accept(self, user):
        """Aceita o convite e cria o membership"""
        if not self.is_pending:
            raise ValueError('Convite não está pendente ou expirou')
        
        # Cria o membership
        membership = AccountMembership.objects.create(
            account=self.account,
            user=user,
            role=self.role,
            status='active',
            can_invite_users=self.can_invite_users,
            can_manage_billing=self.can_manage_billing,
            can_manage_settings=self.can_manage_settings,
            can_view_analytics=self.can_view_analytics,
            invited_by=self.invited_by,
            invited_at=self.created_at,
            joined_at=timezone.now()
        )
        
        # Atualiza o convite
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return membership
    
    def decline(self):
        """Recusa o convite"""
        self.status = 'declined'
        self.save()
    
    def cancel(self):
        """Cancela o convite"""
        self.status = 'cancelled'
        self.save()
    
    def save(self, *args, **kwargs):
        # Gera token se não existir
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(32)
        
        # Define data de expiração se não existir
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
