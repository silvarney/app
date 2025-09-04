from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Plan(models.Model):
    """Modelo para planos de assinatura"""
    
    PLAN_TYPES = [
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Empresarial'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('lifetime', 'Vitalício'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    
    plan_type = models.CharField(
        'Tipo de Plano',
        max_length=20,
        choices=PLAN_TYPES,
        default='basic'
    )
    
    # Preços
    price = models.DecimalField(
        'Preço',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    setup_fee = models.DecimalField(
        'Taxa de Configuração',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    billing_cycle = models.CharField(
        'Ciclo de Cobrança',
        max_length=20,
        choices=BILLING_CYCLES,
        default='monthly'
    )
    
    # Limites do plano
    max_users = models.PositiveIntegerField('Máximo de Usuários', default=1)
    max_storage_gb = models.PositiveIntegerField('Armazenamento (GB)', default=1)
    max_domains = models.PositiveIntegerField('Máximo de Domínios', default=1)
    max_api_calls = models.PositiveIntegerField('Máximo de Chamadas API', default=1000)
    
    # Recursos incluídos
    features = models.JSONField('Recursos', default=dict, blank=True)
    
    # Configurações
    trial_days = models.PositiveIntegerField('Dias de Trial', default=0)
    is_active = models.BooleanField('Ativo', default=True)
    is_featured = models.BooleanField('Destaque', default=False)
    
    # Ordem de exibição
    sort_order = models.PositiveIntegerField('Ordem', default=0)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['sort_order', 'price']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['plan_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()}"
    
    @property
    def is_free(self):
        return self.price == 0 or self.plan_type == 'free'
    
    @property
    def monthly_price(self):
        """Converte o preço para valor mensal para comparação"""
        if self.billing_cycle == 'monthly':
            return self.price
        elif self.billing_cycle == 'quarterly':
            return self.price / 3
        elif self.billing_cycle == 'yearly':
            return self.price / 12
        return self.price


class Subscription(models.Model):
    """Modelo para assinaturas"""
    
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Ativa'),
        ('past_due', 'Em Atraso'),
        ('canceled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('suspended', 'Suspensa'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Conta'
    )
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='Plano'
    )
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )
    
    # Datas importantes
    started_at = models.DateTimeField('Iniciada em', default=timezone.now)
    trial_ends_at = models.DateTimeField('Trial termina em', null=True, blank=True)
    current_period_start = models.DateTimeField('Período atual inicia em')
    current_period_end = models.DateTimeField('Período atual termina em')
    canceled_at = models.DateTimeField('Cancelada em', null=True, blank=True)
    ends_at = models.DateTimeField('Termina em', null=True, blank=True)
    
    # Configurações de cobrança
    auto_renew = models.BooleanField('Renovação Automática', default=True)
    
    # Preços no momento da assinatura (para histórico)
    price_snapshot = models.DecimalField(
        'Preço na Assinatura',
        max_digits=10,
        decimal_places=2
    )
    
    # Metadados
    metadata = models.JSONField('Metadados', default=dict, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['current_period_end']),
        ]
    
    def __str__(self):
        return f"{self.account.name} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_trial(self):
        return self.status == 'trial'
    
    @property
    def is_expired(self):
        if self.ends_at:
            return timezone.now() > self.ends_at
        return False
    
    @property
    def days_until_renewal(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    def cancel(self, at_period_end=True):
        """Cancela a assinatura"""
        self.canceled_at = timezone.now()
        if at_period_end:
            self.ends_at = self.current_period_end
        else:
            self.status = 'canceled'
            self.ends_at = timezone.now()
        self.auto_renew = False
        self.save()
    
    def reactivate(self):
        """Reativa uma assinatura cancelada"""
        if self.status == 'canceled' and not self.is_expired:
            self.status = 'active'
            self.canceled_at = None
            self.ends_at = None
            self.auto_renew = True
            self.save()


class Payment(models.Model):
    """Modelo para pagamentos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('canceled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('partially_refunded', 'Parcialmente Reembolsado'),
    ]
    
    PAYMENT_METHODS = [
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('bank_transfer', 'Transferência Bancária'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Assinatura'
    )
    
    # Valores
    amount = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField('Moeda', max_length=3, default='BRL')
    
    # Status e método
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    payment_method = models.CharField(
        'Método de Pagamento',
        max_length=20,
        choices=PAYMENT_METHODS
    )
    
    # Informações do gateway
    gateway_transaction_id = models.CharField(
        'ID da Transação no Gateway',
        max_length=200,
        blank=True
    )
    
    gateway_response = models.JSONField(
        'Resposta do Gateway',
        default=dict,
        blank=True
    )
    
    # Datas importantes
    due_date = models.DateTimeField('Vencimento', null=True, blank=True)
    paid_at = models.DateTimeField('Pago em', null=True, blank=True)
    failed_at = models.DateTimeField('Falhou em', null=True, blank=True)
    
    # Informações adicionais
    description = models.TextField('Descrição', blank=True)
    invoice_url = models.URLField('URL da Fatura', blank=True)
    receipt_url = models.URLField('URL do Recibo', blank=True)
    
    # Tentativas de cobrança
    attempt_count = models.PositiveIntegerField('Tentativas', default=0)
    max_attempts = models.PositiveIntegerField('Máximo de Tentativas', default=3)
    
    # Metadados
    metadata = models.JSONField('Metadados', default=dict, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['gateway_transaction_id']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Pagamento {self.amount} - {self.subscription.account.name}"
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        if self.due_date and self.status == 'pending':
            return timezone.now() > self.due_date
        return False
    
    @property
    def can_retry(self):
        return (
            self.status in ['pending', 'failed'] and
            self.attempt_count < self.max_attempts
        )
    
    def mark_as_paid(self):
        """Marca o pagamento como pago"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, reason=None):
        """Marca o pagamento como falhou"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        self.attempt_count += 1
        if reason:
            self.metadata['failure_reason'] = reason
        self.save()


class Invoice(models.Model):
    """Modelo para faturas"""
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('open', 'Aberta'),
        ('paid', 'Paga'),
        ('void', 'Anulada'),
        ('uncollectible', 'Incobrável'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name='Assinatura'
    )
    
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice',
        verbose_name='Pagamento'
    )
    
    # Numeração
    invoice_number = models.CharField('Número da Fatura', max_length=50, unique=True)
    
    # Valores
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField('Impostos', max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2)
    
    currency = models.CharField('Moeda', max_length=3, default='BRL')
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Datas
    issue_date = models.DateField('Data de Emissão')
    due_date = models.DateField('Data de Vencimento')
    paid_date = models.DateField('Data de Pagamento', null=True, blank=True)
    
    # Informações adicionais
    description = models.TextField('Descrição', blank=True)
    notes = models.TextField('Observações', blank=True)
    
    # Arquivos
    pdf_file = models.FileField('Arquivo PDF', upload_to='invoices/', blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Fatura'
        verbose_name_plural = 'Faturas'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Fatura {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Gerar número da fatura automaticamente
            from django.utils import timezone
            now = timezone.now()
            count = Invoice.objects.filter(
                created_at__year=now.year,
                created_at__month=now.month
            ).count() + 1
            self.invoice_number = f"{now.year}{now.month:02d}{count:04d}"
        super().save(*args, **kwargs)
