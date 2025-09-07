from django import forms
from django.contrib.auth.models import User
from accounts.models import Account
from .models import Site, TemplateCategory, PlanType, Subscription, Payment


class SiteForm(forms.ModelForm):
    """Formulário para criação e edição de sites"""
    
    class Meta:
        model = Site
        fields = ['domain', 'account', 'template_category', 'plan_type', 'status']
        widgets = {
            'domain': forms.URLInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'placeholder': 'https://exemplo.com'
            }),
            'account': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'template_category': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'plan_type': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            })
        }
        labels = {
            'domain': 'Domínio',
            'account': 'Conta',
            'template_category': 'Categoria do Template',
            'plan_type': 'Tipo de Plano',
            'status': 'Status'
        }
        help_texts = {
            'domain': 'URL completa do site (ex: https://meusite.com)',
            'account': 'Conta proprietária do site',
            'template_category': 'Categoria do template a ser usado',
            'plan_type': 'Plano de assinatura do site',
            'status': 'Status atual do site'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_admin_panel = kwargs.pop('is_admin_panel', False)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset das contas baseado no contexto
        if is_admin_panel and user and user.is_staff:
            # Admin pode ver todas as contas ativas
            self.fields['account'].queryset = Account.objects.filter(status='active')
        elif user:
            # Usuário comum só vê suas contas
            self.fields['account'].queryset = Account.objects.filter(
                memberships__user=user,
                memberships__role__in=['owner', 'admin'],
                memberships__status='active'
            ).distinct()
        
        # Configurar querysets para outros campos
        self.fields['template_category'].queryset = TemplateCategory.objects.all()
        self.fields['plan_type'].queryset = PlanType.objects.filter(is_active=True)
        
        # Tornar template_category opcional
        self.fields['template_category'].required = False
        self.fields['template_category'].empty_label = "Selecione uma categoria (opcional)"
    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        if domain:
            # Verificar se o domínio já existe (exceto para o próprio objeto em edição)
            existing_site = Site.objects.filter(domain=domain)
            if self.instance.pk:
                existing_site = existing_site.exclude(pk=self.instance.pk)
            
            if existing_site.exists():
                raise forms.ValidationError('Este domínio já está sendo usado por outro site.')
        
        return domain


class SubscriptionForm(forms.ModelForm):
    """Formulário para criação e edição de assinaturas"""
    
    class Meta:
        model = Subscription
        fields = ['site', 'account', 'plan_type', 'discount', 'payment_link', 'status']
        widgets = {
            'site': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'account': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'plan_type': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'payment_link': forms.URLInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'placeholder': 'https://exemplo.com/pagamento'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            })
        }
        labels = {
            'site': 'Site',
            'account': 'Conta',
            'plan_type': 'Tipo de Plano',
            'discount': 'Desconto (%)',
            'payment_link': 'Link de Pagamento',
            'status': 'Status'
        }
        help_texts = {
            'site': 'Site associado à assinatura',
            'account': 'Conta proprietária da assinatura',
            'plan_type': 'Plano selecionado para a assinatura',
            'discount': 'Percentual de desconto aplicado (0-100%)',
            'payment_link': 'Link para pagamento da assinatura',
            'status': 'Status atual da assinatura'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar querysets
        self.fields['site'].queryset = Site.objects.filter(status='active')
        self.fields['account'].queryset = Account.objects.filter(status='active')
        self.fields['plan_type'].queryset = PlanType.objects.filter(is_active=True)
        
        # Tornar campos opcionais
        self.fields['payment_link'].required = False
        self.fields['discount'].required = False


class PaymentForm(forms.ModelForm):
    """Formulário para criação e edição de pagamentos"""
    
    class Meta:
        model = Payment
        fields = ['subscription', 'title', 'items_list', 'value', 'discount', 'total_value', 'payment_month', 'payment_year', 'status']
        widgets = {
            'subscription': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'title': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'placeholder': 'Título do pagamento'
            }),
            'items_list': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'rows': 4,
                'placeholder': 'Lista dos itens do pagamento'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'total_value': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'payment_month': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'min': '1',
                'max': '12'
            }),
            'payment_year': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm',
                'min': '2020'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            })
        }
        labels = {
            'subscription': 'Assinatura',
            'title': 'Título',
            'items_list': 'Lista dos Itens',
            'value': 'Valor',
            'discount': 'Desconto',
            'total_value': 'Valor Total',
            'payment_month': 'Mês do Pagamento',
            'payment_year': 'Ano do Pagamento',
            'status': 'Status'
        }
        help_texts = {
            'subscription': 'Assinatura associada ao pagamento',
            'title': 'Título descritivo do pagamento',
            'items_list': 'Descrição detalhada dos itens incluídos',
            'value': 'Valor base do pagamento',
            'discount': 'Valor do desconto aplicado',
            'total_value': 'Valor final após desconto',
            'payment_month': 'Mês de referência (1-12)',
            'payment_year': 'Ano de referência',
            'status': 'Status atual do pagamento'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset
        self.fields['subscription'].queryset = Subscription.objects.select_related('site', 'account').all()
    
    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get('value', 0)
        discount = cleaned_data.get('discount', 0)
        total_value = cleaned_data.get('total_value', 0)
        
        # Calcular valor total automaticamente se não foi fornecido
        if value and discount is not None:
            calculated_total = value - discount
            if total_value != calculated_total:
                cleaned_data['total_value'] = calculated_total
        
        return cleaned_data