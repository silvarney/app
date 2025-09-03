from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django import forms
import json

from users.models import User
from accounts.models import Account, AccountMembership, AccountInvitation
from permissions.models import Permission, Role, UserRole


def admin_login_redirect(request):
    """Redireciona /admin/login/ para /login/"""
    return redirect('/login/')


@login_required
def dashboard(request):
    """Dashboard principal do painel administrativo"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    # Estatísticas gerais
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_accounts = Account.objects.count()
    active_accounts = Account.objects.filter(status='active').count()
    
    # Estatísticas dos últimos 30 dias
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_accounts_30d = Account.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Contas por status
    accounts_by_status = Account.objects.values('status').annotate(count=Count('id'))
    
    # Usuários recentes
    recent_users = User.objects.select_related().order_by('-date_joined')[:10]
    
    # Contas recentes
    recent_accounts = Account.objects.select_related('owner').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'new_users_30d': new_users_30d,
        'new_accounts_30d': new_accounts_30d,
        'accounts_by_status': accounts_by_status,
        'recent_users': recent_users,
        'recent_accounts': recent_accounts,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def users_list(request):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Lista de usuários com filtros e paginação"""
    users = User.objects.select_related().order_by('-date_joined')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    is_staff = request.GET.get('is_staff', '')
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if status:
        if status == 'active':
            users = users.filter(is_active=True)
        elif status == 'inactive':
            users = users.filter(is_active=False)
    
    if is_staff:
        if is_staff == 'yes':
            users = users.filter(is_staff=True)
        elif is_staff == 'no':
            users = users.filter(is_staff=False)
    
    # Paginação
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'is_staff': is_staff,
    }
    
    return render(request, 'admin_panel/users/list.html', context)


@login_required
def user_detail(request, user_id):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Detalhes de um usuário específico"""
    user = get_object_or_404(User, id=user_id)
    
    # Memberships do usuário
    memberships = AccountMembership.objects.filter(user=user).select_related('account')
    
    # Roles do usuário
    user_roles = UserRole.objects.filter(user=user).select_related('role', 'account')
    
    # Convites pendentes
    pending_invitations = AccountInvitation.objects.filter(
        email=user.email,
        status='pending'
    ).select_related('account', 'invited_by')
    
    context = {
        'user': user,
        'memberships': memberships,
        'user_roles': user_roles,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, 'admin_panel/users/detail.html', context)


@login_required
def accounts_list(request):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Lista de contas com filtros e paginação"""
    accounts = Account.objects.select_related('owner').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    plan = request.GET.get('plan', '')
    
    if search:
        accounts = accounts.filter(
            Q(name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(owner__email__icontains=search)
        )
    
    if status:
        accounts = accounts.filter(status=status)
    
    if plan:
        accounts = accounts.filter(plan=plan)
    
    # Paginação
    paginator = Paginator(accounts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'plan': plan,
        'status_choices': Account.STATUS_CHOICES,
        'plan_choices': Account.PLAN_CHOICES,
    }
    
    return render(request, 'admin_panel/accounts/list.html', context)


@login_required
def account_detail(request, account_id):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Detalhes de uma conta específica"""
    account = get_object_or_404(Account, id=account_id)
    
    # Membros da conta
    memberships = AccountMembership.objects.filter(account=account).select_related('user')
    
    # Convites pendentes
    pending_invitations = AccountInvitation.objects.filter(
        account=account,
        status='pending'
    ).select_related('invited_by')
    
    # Roles da conta
    account_roles = Role.objects.filter(account=account)
    
    context = {
        'account': account,
        'memberships': memberships,
        'pending_invitations': pending_invitations,
        'account_roles': account_roles,
    }
    
    return render(request, 'admin_panel/accounts/detail.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Ativar/desativar usuário via AJAX"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    action = 'ativado' if user.is_active else 'desativado'
    messages.success(request, f'Usuário {user.get_full_name()} foi {action} com sucesso.')
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Usuário {action} com sucesso.'
    })


@login_required
@require_http_methods(["POST"])
def toggle_account_status(request, account_id):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Alterar status da conta via AJAX"""
    account = get_object_or_404(Account, id=account_id)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in dict(Account.STATUS_CHOICES):
            account.status = new_status
            account.save()
            
            messages.success(request, f'Status da conta {account.name} alterado para {account.get_status_display()}.')
            
            return JsonResponse({
                'success': True,
                'status': account.status,
                'status_display': account.get_status_display(),
                'message': 'Status alterado com sucesso.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Status inválido.'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos.'
        }, status=400)


@login_required
def roles_list(request):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Lista de roles do sistema"""
    roles = Role.objects.select_related('account').prefetch_related('permissions').order_by('name')
    
    # Filtros
    search = request.GET.get('search', '')
    role_type = request.GET.get('type', '')
    account_id = request.GET.get('account', '')
    
    if search:
        roles = roles.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    if role_type:
        roles = roles.filter(role_type=role_type)
    
    if account_id:
        roles = roles.filter(account_id=account_id)
    
    # Paginação
    paginator = Paginator(roles, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contas para filtro
    accounts = Account.objects.filter(status='active').order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_type': role_type,
        'account_id': account_id,
        'accounts': accounts,
        'type_choices': Role.ROLE_TYPES,
    }
    
    return render(request, 'admin_panel/roles/list.html', context)


@login_required
def permissions_list(request):
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    """Lista de permissões do sistema"""
    permissions = Permission.objects.order_by('category', 'name')
    
    # Filtros
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    permission_type = request.GET.get('type', '')
    
    if search:
        permissions = permissions.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(resource__icontains=search)
        )
    
    if category:
        permissions = permissions.filter(category=category)
    
    if permission_type:
        permissions = permissions.filter(type=permission_type)
    
    # Paginação
    paginator = Paginator(permissions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorias para filtro
    categories = Permission.objects.values_list('category', flat=True).distinct().order_by('category')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'permission_type': permission_type,
        'categories': categories,
        'type_choices': Permission.TYPE_CHOICES,
    }
    
    return render(request, 'admin_panel/permissions/list.html', context)




# Formulário customizado para usuários
class UserForm(forms.ModelForm):
    USER_TYPE_CHOICES = [
        ('user', 'Usuário Comum'),
        ('admin', 'Administrador'),
        ('superadmin', 'Super Administrador'),
    ]
    
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nome completo'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Deixe em branco para gerar uma senha temporária'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Confirme a nova senha'
    )
    user_type = forms.ChoiceField(
        choices=[],  # Será definido no __init__
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        label='Tipo de Usuário',
        initial='user',
        required=False  # Deixamos nossa validação personalizada cuidar disso
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'is_active', 'status', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Definir as opções de tipo de usuário baseado nas permissões do usuário atual
        if self.current_user:
            if self.current_user.is_superuser:
                # Superadmin pode criar qualquer tipo
                self.fields['user_type'].choices = [('', 'Selecione o tipo de usuário')] + self.USER_TYPE_CHOICES
            elif self.current_user.is_staff:
                # Admin pode criar admin ou usuário comum
                self.fields['user_type'].choices = [
                    ('', 'Selecione o tipo de usuário'),
                    ('user', 'Usuário Comum'),
                    ('admin', 'Administrador'),
                ]
            else:
                # Usuário comum não pode criar outros usuários
                self.fields['user_type'].choices = []
                self.fields['user_type'].widget = forms.HiddenInput()
        
        # Definir 'user' como padrão para novos usuários
        if not self.instance.pk:
            self.fields['user_type'].initial = 'user'
        
        # Se estamos editando um usuário existente, definir o tipo atual e preencher o campo name
        if self.instance and self.instance.pk:
            # Preencher o campo name com first_name + last_name
            full_name = f"{self.instance.first_name} {self.instance.last_name}".strip()
            self.fields['name'].initial = full_name
            
            if self.instance.is_superuser:
                self.fields['user_type'].initial = 'superadmin'
            elif self.instance.is_staff:
                self.fields['user_type'].initial = 'admin'
            else:
                self.fields['user_type'].initial = 'user'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Processar o campo 'name' e dividir em first_name e last_name
        name = self.cleaned_data.get('name', '')
        if name:
            name_parts = name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user_type = self.cleaned_data.get('user_type')
        
        # Definir permissões baseado no tipo de usuário
        if user_type == 'superadmin':
            user.is_staff = True
            user.is_superuser = True
        elif user_type == 'admin':
            user.is_staff = True
            user.is_superuser = False
        else:  # user
            user.is_staff = False
            user.is_superuser = False
        
        if commit:
            user.save()
        return user
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            raise forms.ValidationError('As senhas não coincidem.')
        
        # Validar se user_type foi selecionado
        user_type = cleaned_data.get('user_type')
        if not user_type:
            raise forms.ValidationError('Você deve selecionar um tipo de usuário.')
        
        return cleaned_data


@login_required
def user_create(request):
    """Criar novo usuário"""
    # Verificar se o usuário é staff ou superuser
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Você não tem permissão para criar usuários.')
        return redirect('/login/')
    
    if request.method == 'POST':
        form = UserForm(request.POST, current_user=request.user)
        
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            else:
                # Senha padrão temporária
                user.set_password('temp123456')
            user.save()
            
            messages.success(request, f'Usuário {user.get_full_name()} criado com sucesso!')
            return redirect('admin_panel:users_list')
    else:
        form = UserForm(current_user=request.user)
    
    context = {
        'form': form,
        'title': 'Criar Novo Usuário',
        'action': 'create'
    }
    
    return render(request, 'admin_panel/users/form.html', context)


@login_required
@require_http_methods(["POST"])
def account_delete(request, account_id):
    """Excluir conta - apenas proprietários podem excluir suas próprias contas"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    
    account = get_object_or_404(Account, id=account_id)
    
    # Verificar se o usuário atual é o proprietário da conta
    if account.owner != request.user:
        # Apenas superusuários podem excluir contas de outros usuários
        if not request.user.is_superuser:
            messages.error(request, 'Apenas proprietários podem excluir suas próprias contas.')
            return redirect('admin_panel:accounts_list')
    
    # Verificar se a conta tem outros membros ativos
    active_memberships = AccountMembership.objects.filter(
        account=account,
        status='active'
    ).exclude(user=account.owner).count()
    
    if active_memberships > 0:
        messages.error(request, 
            f'Não é possível excluir a conta "{account.name}" pois ela possui {active_memberships} membro(s) ativo(s). '
            'Remova todos os membros antes de excluir a conta.'
        )
        return redirect('admin_panel:accounts_list')
    
    account_name = account.name
    account.delete()
    messages.success(request, f'Conta "{account_name}" excluída com sucesso!')
    
    return redirect('admin_panel:accounts_list')


@login_required
def user_edit(request, user_id):
    """Editar usuário existente"""
    # Verificar se o usuário é staff ou superuser
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Você não tem permissão para editar usuários.')
        return redirect('/login/')
    
    user = get_object_or_404(User, id=user_id)
    
    # Verificar se o usuário pode editar este tipo de usuário
    if not request.user.is_superuser:
        if user.is_superuser:
            messages.error(request, 'Você não tem permissão para editar um super administrador.')
            return redirect('admin_panel:users_list')
        if not request.user.is_staff and user.is_staff:
            messages.error(request, 'Você não tem permissão para editar um administrador.')
            return redirect('admin_panel:users_list')
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, current_user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, f'Usuário {user.get_full_name()} atualizado com sucesso!')
            return redirect('admin_panel:users_list')
    else:
        form = UserForm(instance=user, current_user=request.user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Editar Usuário - {user.get_full_name()}',
        'action': 'edit'
    }
    
    return render(request, 'admin_panel/users/form.html', context)


@login_required
@require_http_methods(["POST"])
def user_delete(request, user_id):
    """Excluir usuário"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para acessar o painel administrativo.')
        return redirect('/login/')
    
    user = get_object_or_404(User, id=user_id)
    
    # Não permitir exclusão do próprio usuário
    if user == request.user:
        messages.error(request, 'Você não pode excluir sua própria conta.')
        return redirect('admin_panel:users_list')
    
    # Não permitir exclusão de superusuários por usuários não-super
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para excluir superusuários.')
        return redirect('admin_panel:users_list')
    
    user_name = user.get_full_name()
    user.delete()
    messages.success(request, f'Usuário {user_name} excluído com sucesso!')
    
    return redirect('admin_panel:users_list')
