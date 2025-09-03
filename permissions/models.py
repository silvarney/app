from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class Permission(models.Model):
    """Modelo para permissões do sistema"""
    
    PERMISSION_TYPES = [
        ('create', 'Criar'),
        ('read', 'Visualizar'),
        ('update', 'Editar'),
        ('delete', 'Excluir'),
        ('manage', 'Gerenciar'),
        ('admin', 'Administrar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=100, unique=True)
    codename = models.CharField('Código', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    
    # Tipo de permissão
    permission_type = models.CharField(
        'Tipo de Permissão',
        max_length=20,
        choices=PERMISSION_TYPES,
        default='read'
    )
    
    # Recurso ao qual a permissão se aplica
    resource = models.CharField('Recurso', max_length=100)
    
    # Permissão específica para um modelo
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Tipo de Conteúdo',
        related_name='custom_permissions'
    )
    
    # Categoria da permissão
    category = models.CharField('Categoria', max_length=50, default='general')
    
    # Se a permissão está ativa
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Permissão'
        verbose_name_plural = 'Permissões'
        ordering = ['category', 'resource', 'permission_type']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['resource']),
            models.Index(fields=['category']),
            models.Index(fields=['permission_type']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.codename})'
    
    def save(self, *args, **kwargs):
        # Gera codename automaticamente se não fornecido
        if not self.codename:
            self.codename = f'{self.permission_type}_{self.resource}'.lower().replace(' ', '_')
        super().save(*args, **kwargs)


class Role(models.Model):
    """Modelo para funções/papéis do sistema"""
    
    ROLE_TYPES = [
        ('system', 'Sistema'),
        ('account', 'Conta'),
        ('custom', 'Personalizada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=100)
    codename = models.CharField('Código', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    
    # Tipo de função
    role_type = models.CharField(
        'Tipo de Função',
        max_length=20,
        choices=ROLE_TYPES,
        default='custom'
    )
    
    # Permissões da função
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name='Permissões'
    )
    
    # Conta específica (para funções de conta)
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles',
        verbose_name='Conta'
    )
    
    # Hierarquia de funções
    parent_role = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_roles',
        verbose_name='Função Pai'
    )
    
    # Prioridade da função (maior número = maior prioridade)
    priority = models.PositiveIntegerField('Prioridade', default=0)
    
    # Se a função está ativa
    is_active = models.BooleanField('Ativo', default=True)
    
    # Se é uma função padrão do sistema
    is_system = models.BooleanField('Função do Sistema', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Função'
        verbose_name_plural = 'Funções'
        ordering = ['-priority', 'name']
        unique_together = [['name', 'account']]
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['role_type']),
            models.Index(fields=['account']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        if self.account:
            return f'{self.name} ({self.account.name})'
        return self.name
    
    def get_all_permissions(self):
        """Retorna todas as permissões da função, incluindo as herdadas"""
        permissions = set(self.permissions.filter(is_active=True))
        
        # Adiciona permissões da função pai
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())
        
        return permissions
    
    def has_permission(self, permission_codename):
        """Verifica se a função tem uma permissão específica"""
        return self.get_all_permissions().filter(codename=permission_codename).exists()
    
    def save(self, *args, **kwargs):
        # Gera codename automaticamente se não fornecido
        if not self.codename:
            base_codename = self.name.lower().replace(' ', '_')
            if self.account:
                self.codename = f'{self.account.slug}_{base_codename}'
            else:
                self.codename = base_codename
        super().save(*args, **kwargs)


class RolePermission(models.Model):
    """Modelo intermediário para Role e Permission"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name='Função'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        verbose_name='Permissão'
    )
    
    # Condições específicas para a permissão
    conditions = models.JSONField('Condições', default=dict, blank=True)
    
    # Se a permissão está ativa para esta função
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Permissão da Função'
        verbose_name_plural = 'Permissões das Funções'
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['permission', 'is_active']),
        ]
    
    def __str__(self):
        return f'{self.role.name} - {self.permission.name}'


class UserRole(models.Model):
    """Modelo para associar usuários a funções"""
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('suspended', 'Suspenso'),
        ('expired', 'Expirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Usuário'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Função'
    )
    
    # Conta específica (para funções de conta)
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_roles',
        verbose_name='Conta'
    )
    
    # Status da atribuição
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Datas de validade
    valid_from = models.DateTimeField('Válido de', null=True, blank=True)
    valid_until = models.DateTimeField('Válido até', null=True, blank=True)
    
    # Quem atribuiu a função
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name='Atribuído por'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Função do Usuário'
        verbose_name_plural = 'Funções dos Usuários'
        unique_together = ['user', 'role', 'account']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['role', 'status']),
            models.Index(fields=['account', 'status']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        if self.account:
            return f'{self.user.get_full_name() or self.user.username} - {self.role.name} ({self.account.name})'
        return f'{self.user.get_full_name() or self.user.username} - {self.role.name}'
    
    @property
    def is_active(self):
        """Verifica se a atribuição está ativa"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.status != 'active':
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    @property
    def is_expired(self):
        """Verifica se a atribuição expirou"""
        from django.utils import timezone
        if self.valid_until:
            return timezone.now() > self.valid_until
        return False
    
    def activate(self):
        """Ativa a atribuição"""
        self.status = 'active'
        self.save()
    
    def deactivate(self):
        """Desativa a atribuição"""
        self.status = 'inactive'
        self.save()
    
    def suspend(self):
        """Suspende a atribuição"""
        self.status = 'suspended'
        self.save()


class UserPermission(models.Model):
    """Modelo para permissões específicas de usuário (override)"""
    
    GRANT_TYPES = [
        ('grant', 'Conceder'),
        ('deny', 'Negar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_user_permissions',
        verbose_name='Usuário'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='user_permissions',
        verbose_name='Permissão'
    )
    
    # Conta específica
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_permissions',
        verbose_name='Conta'
    )
    
    # Tipo de concessão
    grant_type = models.CharField(
        'Tipo de Concessão',
        max_length=10,
        choices=GRANT_TYPES,
        default='grant'
    )
    
    # Objeto específico (usando GenericForeignKey)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Condições específicas
    conditions = models.JSONField('Condições', default=dict, blank=True)
    
    # Datas de validade
    valid_from = models.DateTimeField('Válido de', null=True, blank=True)
    valid_until = models.DateTimeField('Válido até', null=True, blank=True)
    
    # Quem concedeu a permissão
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions',
        verbose_name='Concedido por'
    )
    
    # Se a permissão está ativa
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Permissão do Usuário'
        verbose_name_plural = 'Permissões dos Usuários'
        unique_together = ['user', 'permission', 'account', 'content_type', 'object_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['permission', 'is_active']),
            models.Index(fields=['account', 'is_active']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        grant_text = 'Conceder' if self.grant_type == 'grant' else 'Negar'
        if self.account:
            return f'{grant_text} {self.permission.name} para {self.user.get_full_name() or self.user.username} ({self.account.name})'
        return f'{grant_text} {self.permission.name} para {self.user.get_full_name() or self.user.username}'
    
    @property
    def is_valid(self):
        """Verifica se a permissão está válida"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
