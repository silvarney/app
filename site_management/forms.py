from django import forms
from django.contrib.auth.models import User
from accounts.models import Account
from .models import Site, TemplateCategory, PlanType


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