from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django import forms
import json
import csv
from collections import defaultdict
from django.contrib.auth import authenticate

from users.models import User
from accounts.models import Account, AccountMembership, AccountInvitation
from permissions.models import Permission, Role, UserRole
from content.models import Content, Category, Tag
from domains.models import Domain


def admin_login_redirect(request):
    """Redireciona /admin/login/ para /"""
    return redirect('/')


@login_required
def dashboard(request):
    """Dashboard principal do painel administrativo"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Lista de usuários com filtros e paginação"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    users = User.objects.select_related().order_by('-date_joined')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    is_staff = request.GET.get('is_staff', '')
    format_type = request.GET.get('format', '')
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(username__icontains=search)
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
    
    # Se for requisição JSON para busca de usuários
    if format_type == 'json':
        # Limitar resultados para busca
        users_data = []
        for user in users[:10]:  # Limitar a 10 resultados
            full_name = f"{user.first_name} {user.last_name}".strip()
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': full_name if full_name else user.username,
                'is_active': user.is_active
            })
        
        return JsonResponse({'users': users_data})
    
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
    """Detalhes de um usuário específico"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Lista de contas com filtros e paginação"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Detalhes de uma conta específica"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Ativar/desativar usuário via AJAX"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Alterar status da conta via AJAX"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
            'message': 'Dados JSON inválidos.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)


@login_required
def permission_detail(request, permission_id):
    """Detalhes de uma permissão específica"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    permission = get_object_or_404(Permission, id=permission_id)
    
    # Buscar roles que possuem esta permissão
    role_permissions = permission.rolepermission_set.filter(is_active=True).select_related('role')
    
    # Buscar usuários que possuem esta permissão diretamente
    user_permissions = permission.userpermission_set.filter(is_active=True).select_related('user', 'account')
    
    context = {
        'permission': permission,
        'role_permissions': role_permissions,
        'user_permissions': user_permissions,
    }
    
    return render(request, 'admin_panel/permissions/detail.html', context)


@login_required
def permission_create(request):
    """Criar nova permissão"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para criar permissões.')
    
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permissão "{permission.name}" criada com sucesso!')
            return redirect('admin_panel:permission_detail', permission_id=permission.id)
    else:
        form = PermissionForm()
    
    context = {
        'form': form,
        'title': 'Criar Nova Permissão',
        'action': 'create'
    }
    
    return render(request, 'admin_panel/permissions/form.html', context)


@login_required
def permission_edit(request, permission_id):
    """Editar permissão existente"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para editar permissões.')
    
    permission = get_object_or_404(Permission, id=permission_id)
    
    # Verificar se é uma permissão de sistema e se o usuário pode editá-la
    if permission.is_system and not request.user.is_superuser:
        raise PermissionDenied('Apenas superusuários podem editar permissões de sistema.')
    
    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permission)
        
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permissão "{permission.name}" atualizada com sucesso!')
            return redirect('admin_panel:permission_detail', permission_id=permission.id)
    else:
        form = PermissionForm(instance=permission)
    
    context = {
        'form': form,
        'permission': permission,
        'title': f'Editar Permissão: {permission.name}',
        'action': 'edit'
    }
    
    return render(request, 'admin_panel/permissions/form.html', context)


@login_required
@require_http_methods(["POST"])
def permission_delete(request, permission_id):
    """Excluir permissão"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para excluir permissões.')
    
    permission = get_object_or_404(Permission, id=permission_id)
    
    # Verificar se é uma permissão de sistema e se o usuário pode excluí-la
    if permission.is_system and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Apenas superusuários podem excluir permissões de sistema.'
        })
    
    # Verificar se há roles ou usuários usando esta permissão
    role_count = permission.rolepermission_set.filter(is_active=True).count()
    user_count = permission.userpermission_set.filter(is_active=True).count()
    
    if role_count > 0 or user_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Não é possível excluir a permissão "{permission.name}" pois está sendo usada por {role_count} role(s) e {user_count} usuário(s).'
        })
    
    try:
        permission_name = permission.name
        permission.delete()
        messages.success(request, f'Permissão "{permission_name}" excluída com sucesso!')
        return JsonResponse({
            'success': True,
            'message': f'Permissão "{permission_name}" excluída com sucesso!',
            'redirect_url': '/admin/permissions/'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir permissão: {str(e)}'
        })


@login_required
def roles_list(request):
    """Lista de roles do sistema"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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
    """Lista de permissões do sistema"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
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


@login_required
def role_detail(request, role_id):
    """Detalhes de uma role específica"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    role = get_object_or_404(Role, id=role_id)
    
    # Buscar usuários com esta role
    user_roles = UserRole.objects.filter(role=role).select_related('user', 'account')
    
    # Buscar permissões da role
    role_permissions = role.rolepermission_set.filter(is_active=True).select_related('permission')
    
    context = {
        'role': role,
        'user_roles': user_roles,
        'role_permissions': role_permissions,
    }
    
    return render(request, 'admin_panel/roles/detail.html', context)


@login_required
def role_create(request):
    """Criar nova role"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para criar roles.')
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" criada com sucesso!')
            return redirect('admin_panel:role_detail', role_id=role.id)
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'title': 'Criar Nova Role',
        'action': 'create'
    }
    
    return render(request, 'admin_panel/roles/form.html', context)


@login_required
def role_edit(request, role_id):
    """Editar role existente"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para editar roles.')
    
    role = get_object_or_404(Role, id=role_id)
    
    # Verificar se é uma role de sistema e se o usuário pode editá-la
    if role.is_system and not request.user.is_superuser:
        raise PermissionDenied('Apenas superusuários podem editar roles de sistema.')
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" atualizada com sucesso!')
            return redirect('admin_panel:role_detail', role_id=role.id)
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'title': f'Editar Role: {role.name}',
        'action': 'edit'
    }
    
    return render(request, 'admin_panel/roles/form.html', context)


@login_required
@require_http_methods(["POST"])
def role_delete(request, role_id):
    """Excluir role"""
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied('Você não tem permissão para excluir roles.')
    
    role = get_object_or_404(Role, id=role_id)
    
    # Verificar se é uma role de sistema e se o usuário pode excluí-la
    if role.is_system and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Apenas superusuários podem excluir roles de sistema.'
        })
    
    # Verificar se há usuários usando esta role
    user_count = UserRole.objects.filter(role=role, status='active').count()
    if user_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Não é possível excluir a role "{role.name}" pois {user_count} usuário(s) ainda a possuem.'
        })
    
    try:
        role_name = role.name
        role.delete()
        messages.success(request, f'Role "{role_name}" excluída com sucesso!')
        return JsonResponse({
            'success': True,
            'message': f'Role "{role_name}" excluída com sucesso!',
            'redirect_url': '/admin/roles/'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir role: {str(e)}'
        })


# Formulário para roles
class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permissões',
        help_text='Selecione as permissões que esta role deve ter'
    )
    
    class Meta:
        model = Role
        fields = ['name', 'codename', 'description', 'role_type', 'priority', 'is_active', 'account']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'codename': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'role_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar contas ativas para o campo account
        self.fields['account'].queryset = Account.objects.filter(status='active')
        self.fields['account'].empty_label = "Role de Sistema (sem conta específica)"
        
        # Se estamos editando uma role existente, carregar suas permissões
        if self.instance and self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.filter(
                rolepermission__is_active=True
            )
    
    def save(self, commit=True):
        role = super().save(commit)
        
        if commit:
            # Limpar permissões existentes
            from permissions.models import RolePermission
            RolePermission.objects.filter(role=role).delete()
            
            # Adicionar novas permissões
            permissions = self.cleaned_data.get('permissions', [])
            for permission in permissions:
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    is_active=True
                )
        
        return role


# Formulário para permissões
class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = [
            'name', 'codename', 'description', 'permission_type', 'resource', 
            'category', 'is_active', 'content_type'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'codename': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permission_type': forms.Select(attrs={'class': 'form-control'}),
            'resource': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar content_type opcional
        self.fields['content_type'].required = False
        self.fields['content_type'].empty_label = "Nenhum (permissão geral)"
        
        # Adicionar help texts
        self.fields['codename'].help_text = 'Nome único da permissão (ex: create_user, edit_content)'
        self.fields['resource'].help_text = 'Recurso ao qual a permissão se aplica (ex: user, content, account)'
        self.fields['category'].help_text = 'Categoria da permissão para organização (ex: user_management, content_management)'


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
        raise PermissionDenied('Você não tem permissão para criar usuários.')
    
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
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
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
        raise PermissionDenied('Você não tem permissão para editar usuários.')
    
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
    """Excluir usuário com opções de soft delete e hard delete"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    user = get_object_or_404(User.all_objects, id=user_id)  # Usar all_objects para incluir soft deleted
    
    # Não permitir exclusão do próprio usuário
    if user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'Você não pode excluir sua própria conta.'
        })
    
    # Não permitir exclusão de superusuários por usuários não-super
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Você não tem permissão para excluir superusuários.'
        })
    
    try:
        data = json.loads(request.body)
        delete_type = data.get('delete_type', 'soft')  # 'soft' ou 'hard'
        account_transfers = data.get('account_transfers', {})
        admin_password = data.get('admin_password')
        
        user_name = user.get_full_name() or user.username
        
        # Para hard delete, validar senha do administrador
        if delete_type == 'hard':
            if not admin_password:
                return JsonResponse({
                    'success': False,
                    'message': 'Senha do administrador é obrigatória para exclusão permanente.'
                })
            
            if not request.user.check_password(admin_password):
                return JsonResponse({
                    'success': False,
                    'message': 'Senha do administrador incorreta.'
                })
        
        # Verificar contas associadas
        owned_accounts = user.owned_accounts.all()
        
        if owned_accounts.exists():
            # Para soft delete, sempre exigir transferência de contas
            if delete_type == 'soft':
                if not account_transfers:
                    account_names = ', '.join([acc.name for acc in owned_accounts[:3]])
                    if owned_accounts.count() > 3:
                        account_names += f' e mais {owned_accounts.count() - 3} contas'
                    
                    return JsonResponse({
                        'success': False,
                        'message': f'O usuário "{user_name}" é proprietário das seguintes contas: {account_names}. Selecione um usuário para transferir a propriedade.',
                        'has_accounts': True,
                        'accounts': [{'id': acc.id, 'name': acc.name} for acc in owned_accounts]
                    })
                
                # Transferir propriedade das contas individualmente
                for account in owned_accounts:
                    account_id_str = str(account.id)
                    if account_id_str in account_transfers:
                        transfer_user_id = account_transfers[account_id_str]
                        transfer_user = get_object_or_404(User, id=transfer_user_id)
                        account.owner = transfer_user
                        account.save()
            
            # Para hard delete, as contas serão excluídas junto com o usuário
            # Não é necessário transferir propriedade
        
        # Executar exclusão baseada no tipo
        if delete_type == 'soft':
            user.soft_delete()
            message = f'Usuário "{user_name}" foi desativado com sucesso (soft delete).'
        else:  # hard delete
            # Para hard delete, excluir também as contas que foram transferidas
            if owned_accounts.exists():
                for account in owned_accounts:
                    # Excluir todos os relacionamentos da conta
                    account.memberships.all().delete()
                    account.invitations.all().delete()
                    account.roles.all().delete()
                    account.delete()
            
            # Excluir relacionamentos do usuário
            user.user_roles.all().delete()
            user.memberships.all().delete()
            user.sent_invitations.all().delete()
            user.sent_account_invitations.all().delete()
            
            # Exclusão permanente
            user.hard_delete()
            message = f'Usuário "{user_name}" foi excluído permanentemente com sucesso.'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos enviados.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir usuário: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def check_user_accounts(request, user_id):
    """Verificar contas associadas a um usuário e retornar usuários disponíveis para transferência"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    user = get_object_or_404(User.all_objects, id=user_id)
    owned_accounts = user.owned_accounts.all()
    
    # Buscar usuários disponíveis para transferência (excluindo o usuário atual e usuários soft deleted)
    available_users = User.objects.filter(
        is_active=True
    ).exclude(
        id__in=[user_id, request.user.id]
    ).prefetch_related('owned_accounts', 'memberships__account')
    
    # Obter IDs das contas do usuário sendo excluído
    user_account_ids = set(owned_accounts.values_list('id', flat=True))
    
    # Formatar nomes dos usuários e identificar aqueles que fazem parte das mesmas contas
    formatted_users = []
    for u in available_users:
        full_name = f"{u.first_name} {u.last_name}".strip()
        display_name = full_name if full_name else u.username
        
        # Verificar se o usuário faz parte de alguma das contas do usuário sendo excluído
        user_accounts = set(u.owned_accounts.values_list('id', flat=True)) | set(u.memberships.values_list('account_id', flat=True))
        is_same_account = bool(user_account_ids & user_accounts)
        
        formatted_users.append({
            'id': u.id,
            'display_name': display_name,
            'email': u.email,
            'is_same_account': is_same_account
        })
    
    # Ordenar usuários: primeiro os da mesma conta, depois os outros
    formatted_users.sort(key=lambda x: (not x['is_same_account'], x['display_name']))
    
    return JsonResponse({
        'success': True,
        'has_accounts': owned_accounts.exists(),
        'accounts': [{'id': acc.id, 'name': acc.name} for acc in owned_accounts],
        'available_users': formatted_users
    })


@login_required
def analytics_dashboard(request):
    """Dashboard de análises avançadas"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    # Período de análise (padrão: últimos 30 dias)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Estatísticas de crescimento
    users_growth = []
    accounts_growth = []
    
    for i in range(days, 0, -1):
        date = timezone.now() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        users_count = User.objects.filter(date_joined__lt=date_end).count()
        accounts_count = Account.objects.filter(created_at__lt=date_end).count()
        
        users_growth.append({
            'date': date_start.strftime('%Y-%m-%d'),
            'count': users_count
        })
        accounts_growth.append({
            'date': date_start.strftime('%Y-%m-%d'),
            'count': accounts_count
        })
    
    # Distribuição por planos
    plan_distribution = Account.objects.values('plan').annotate(count=Count('id')).order_by('plan')
    
    # Distribuição por status
    status_distribution = Account.objects.values('status').annotate(count=Count('id')).order_by('status')
    
    # Top contas por número de membros
    top_accounts = Account.objects.annotate(
        member_count=Count('memberships')
    ).order_by('-member_count')[:10]
    
    # Usuários mais ativos (por número de contas)
    active_users = User.objects.annotate(
        account_count=Count('owned_accounts')
    ).filter(account_count__gt=0).order_by('-account_count')[:10]
    
    context = {
        'days': days,
        'users_growth': json.dumps(users_growth),
        'accounts_growth': json.dumps(accounts_growth),
        'plan_distribution': plan_distribution,
        'status_distribution': status_distribution,
        'top_accounts': top_accounts,
        'active_users': active_users,
    }
    
    return render(request, 'admin_panel/analytics/dashboard.html', context)


@login_required
def export_users(request):
    """Exportar lista de usuários em CSV"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="usuarios_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nome', 'Sobrenome', 'Email', 'Telefone', 'Ativo', 
        'Staff', 'Superuser', 'Data de Cadastro', 'Último Login', 'Tipo de Usuário'
    ])
    
    users = User.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            user.id,
            user.first_name,
            user.last_name,
            user.email,
            user.phone or '',
            'Sim' if user.is_active else 'Não',
            'Sim' if user.is_staff else 'Não',
            'Sim' if user.is_superuser else 'Não',
            user.date_joined.strftime('%d/%m/%Y %H:%M'),
            user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca',
            user.get_user_type_display() if hasattr(user, 'get_user_type_display') else 'N/A'
        ])
    
    return response


@login_required
def export_accounts(request):
    """Exportar lista de contas em CSV"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="contas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nome', 'Empresa', 'Proprietário', 'Email do Proprietário', 
        'Plano', 'Status', 'Data de Criação', 'Número de Membros'
    ])
    
    accounts = Account.objects.select_related('owner').annotate(
        member_count=Count('memberships')
    ).order_by('-created_at')
    
    for account in accounts:
        writer.writerow([
            str(account.id),
            account.name,
            account.company_name or '',
            account.owner.get_full_name(),
            account.owner.email,
            account.get_plan_display(),
            account.get_status_display(),
            account.created_at.strftime('%d/%m/%Y %H:%M'),
            account.member_count
        ])
    
    return response


@login_required
def system_health(request):
    """Verificação de saúde do sistema"""
    # Verificar se o usuário é staff
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    # Verificações de saúde
    health_checks = []
    
    # Verificar usuários órfãos (sem contas)
    orphan_users = User.objects.filter(
        owned_accounts__isnull=True,
        memberships__isnull=True
    ).count()
    
    health_checks.append({
        'name': 'Usuários Órfãos',
        'status': 'warning' if orphan_users > 0 else 'success',
        'value': orphan_users,
        'description': 'Usuários sem contas associadas'
    })
    
    # Verificar contas sem membros
    empty_accounts = Account.objects.filter(
        memberships__isnull=True
    ).count()
    
    health_checks.append({
        'name': 'Contas Vazias',
        'status': 'warning' if empty_accounts > 0 else 'success',
        'value': empty_accounts,
        'description': 'Contas sem membros'
    })
    
    # Verificar convites pendentes antigos (mais de 7 dias)
    old_invitations = AccountInvitation.objects.filter(
        status='pending',
        created_at__lt=timezone.now() - timedelta(days=7)
    ).count()
    
    health_checks.append({
        'name': 'Convites Antigos',
        'status': 'warning' if old_invitations > 0 else 'success',
        'value': old_invitations,
        'description': 'Convites pendentes há mais de 7 dias'
    })
    
    # Verificar usuários inativos
    inactive_users = User.objects.filter(is_active=False).count()
    
    health_checks.append({
        'name': 'Usuários Inativos',
        'status': 'info',
        'value': inactive_users,
        'description': 'Usuários desativados no sistema'
    })
    
    # Verificar contas suspensas
    suspended_accounts = Account.objects.filter(status='suspended').count()
    
    health_checks.append({
        'name': 'Contas Suspensas',
        'status': 'warning' if suspended_accounts > 0 else 'success',
        'value': suspended_accounts,
        'description': 'Contas com status suspenso'
    })
    
    context = {
        'health_checks': health_checks,
        'last_check': timezone.now()
    }
    
    return render(request, 'admin_panel/system/health.html', context)


# ===== CONTENT MANAGEMENT VIEWS =====

@login_required
def content_list(request):
    """Lista de conteúdos com filtros e paginação"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    contents = Content.objects.select_related('account', 'author', 'category').prefetch_related('tags').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    account = request.GET.get('account', '')
    
    if search:
        contents = contents.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(author__email__icontains=search)
        )
    
    if status:
        contents = contents.filter(status=status)
    
    if category:
        contents = contents.filter(category_id=category)
    
    if account:
        contents = contents.filter(account_id=account)
    
    # Paginação
    paginator = Paginator(contents, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    categories = Category.objects.all().order_by('name')
    accounts = Account.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'category': category,
        'account': account,
        'categories': categories,
        'accounts': accounts,
        'status_choices': Content.STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/content/list.html', context)


@login_required
def content_detail(request, content_id):
    """Detalhes de um conteúdo específico"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    content = get_object_or_404(Content, id=content_id)
    
    context = {
        'content': content,
    }
    
    return render(request, 'admin_panel/content/detail.html', context)


@login_required
@require_http_methods(["POST"])
def content_toggle_status(request, content_id):
    """Alterna o status de um conteúdo (publicado/rascunho)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    content = get_object_or_404(Content, id=content_id)
    
    if content.status == 'published':
        content.status = 'draft'
        message = 'Conteúdo movido para rascunho'
    else:
        content.status = 'published'
        content.published_at = timezone.now()
        message = 'Conteúdo publicado'
    
    content.save()
    
    return JsonResponse({
        'success': True,
        'message': message,
        'new_status': content.status
    })


@login_required
@require_http_methods(["POST"])
def content_delete(request, content_id):
    """Exclui um conteúdo"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    content = get_object_or_404(Content, id=content_id)
    content_title = content.title
    content.delete()
    
    messages.success(request, f'Conteúdo "{content_title}" excluído com sucesso.')
    
    return JsonResponse({
        'success': True,
        'message': f'Conteúdo "{content_title}" excluído com sucesso.'
    })


@login_required
def categories_list(request):
    """Lista de categorias com filtros e paginação"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    categories = Category.objects.select_related('account').annotate(
        content_count=Count('contents')
    ).order_by('name')
    
    # Filtros
    search = request.GET.get('search', '')
    account = request.GET.get('account', '')
    
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if account:
        categories = categories.filter(account_id=account)
    
    # Paginação
    paginator = Paginator(categories, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    accounts = Account.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'account': account,
        'accounts': accounts,
    }
    
    return render(request, 'admin_panel/categories/list.html', context)


@login_required
def category_detail(request, category_id):
    """Detalhes de uma categoria específica"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    category = get_object_or_404(Category, id=category_id)
    
    # Conteúdos da categoria
    contents = category.contents.select_related('author').order_by('-created_at')[:10]
    
    context = {
        'category': category,
        'contents': contents,
        'total_contents': category.contents.count(),
    }
    
    return render(request, 'admin_panel/categories/detail.html', context)


@login_required
@require_http_methods(["POST"])
def category_delete(request, category_id):
    """Exclui uma categoria"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    category = get_object_or_404(Category, id=category_id)
    
    # Verificar se há conteúdos associados
    content_count = category.contents.count()
    if content_count > 0:
        return JsonResponse({
            'error': f'Não é possível excluir a categoria. Há {content_count} conteúdo(s) associado(s).'
        }, status=400)
    
    category_name = category.name
    category.delete()
    
    messages.success(request, f'Categoria "{category_name}" excluída com sucesso.')
    
    return JsonResponse({
        'success': True,
        'message': f'Categoria "{category_name}" excluída com sucesso.'
    })


@login_required
def tags_list(request):
    """Lista de tags com filtros e paginação"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    tags = Tag.objects.select_related('account').annotate(
        content_count=Count('contents')
    ).order_by('name')
    
    # Filtros
    search = request.GET.get('search', '')
    account = request.GET.get('account', '')
    
    if search:
        tags = tags.filter(name__icontains=search)
    
    if account:
        tags = tags.filter(account_id=account)
    
    # Paginação
    paginator = Paginator(tags, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    accounts = Account.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'account': account,
        'accounts': accounts,
    }
    
    return render(request, 'admin_panel/tags/list.html', context)


@login_required
def tag_detail(request, tag_id):
    """Detalhes de uma tag específica"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    tag = get_object_or_404(Tag, id=tag_id)
    
    # Conteúdos da tag
    contents = tag.contents.select_related('author', 'category').order_by('-created_at')[:10]
    
    context = {
        'tag': tag,
        'contents': contents,
        'total_contents': tag.contents.count(),
    }
    
    return render(request, 'admin_panel/tags/detail.html', context)


@login_required
@require_http_methods(["POST"])
def tag_delete(request, tag_id):
    """Exclui uma tag"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    tag = get_object_or_404(Tag, id=tag_id)
    tag_name = tag.name
    tag.delete()
    
    messages.success(request, f'Tag "{tag_name}" excluída com sucesso.')
    
    return JsonResponse({
        'success': True,
        'message': f'Tag "{tag_name}" excluída com sucesso.'
    })


@login_required
def domains_list(request):
    """Lista de domínios com filtros e paginação"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    domains = Domain.objects.select_related('account').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    account = request.GET.get('account', '')
    
    if search:
        domains = domains.filter(
            Q(domain__icontains=search) |
            Q(account__name__icontains=search)
        )
    
    if status:
        domains = domains.filter(status=status)
    
    if account:
        domains = domains.filter(account_id=account)
    
    # Paginação
    paginator = Paginator(domains, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    accounts = Account.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'account': account,
        'accounts': accounts,
        'status_choices': Domain.STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/domains/list.html', context)


@login_required
def domain_detail(request, domain_id):
    """Detalhes de um domínio específico"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
    
    domain = get_object_or_404(Domain, id=domain_id)
    
    context = {
        'domain': domain,
    }
    
    return render(request, 'admin_panel/domains/detail.html', context)


@login_required
@require_http_methods(["POST"])
def domain_verify(request, domain_id):
    """Força a verificação de um domínio"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    domain = get_object_or_404(Domain, id=domain_id)
    
    # Simular verificação (implementar lógica real conforme necessário)
    domain.status = 'verified'
    domain.verified_at = timezone.now()
    domain.save()
    
    messages.success(request, f'Domínio "{domain.domain}" verificado com sucesso.')
    
    return JsonResponse({
        'success': True,
        'message': f'Domínio "{domain.domain}" verificado com sucesso.',
        'new_status': domain.status
    })


@login_required
@require_http_methods(["POST"])
def domain_delete(request, domain_id):
    """Exclui um domínio"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    domain = get_object_or_404(Domain, id=domain_id)
    domain_name = domain.domain
    domain.delete()
    
    messages.success(request, f'Domínio "{domain_name}" excluído com sucesso.')
    
    return JsonResponse({
        'success': True,
        'message': f'Domínio "{domain_name}" excluído com sucesso.'
    })


@login_required
def admin_settings_general(request):
    """Configurações gerais do sistema"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    from settings.models import GlobalSetting
    
    if request.method == 'POST':
        # Processar formulário de configurações gerais
        if 'app_name' in request.POST:
            # Salvar configurações gerais
            app_name = request.POST.get('app_name', '')
            base_url = request.POST.get('base_url', '')
            timezone = request.POST.get('timezone', 'America/Sao_Paulo')
            default_language = request.POST.get('default_language', 'pt-br')
            maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            
            # Atualizar ou criar configurações
            settings_to_update = [
                ('site_name', app_name, 'string'),
                ('base_url', base_url, 'string'),
                ('default_timezone', timezone, 'string'),
                ('default_language', default_language, 'string'),
                ('maintenance_mode', str(maintenance_mode).lower(), 'boolean'),
            ]
            
            for key, value, setting_type in settings_to_update:
                setting, created = GlobalSetting.objects.get_or_create(
                    key=key,
                    defaults={
                        'value': value,
                        'setting_type': setting_type,
                        'category': 'general',
                        'description': f'Configuração {key}'
                    }
                )
                if not created:
                    setting.value = value
                    setting.save()
            
            messages.success(request, 'Configurações gerais salvas com sucesso!')
        
        # Processar formulário de configurações de email
        elif 'from_email' in request.POST:
            from_email = request.POST.get('from_email', '')
            from_name = request.POST.get('from_name', '')
            
            # Atualizar configurações de email
            email_settings = [
                ('from_email', from_email, 'string'),
                ('from_name', from_name, 'string'),
            ]
            
            for key, value, setting_type in email_settings:
                setting, created = GlobalSetting.objects.get_or_create(
                    key=key,
                    defaults={
                        'value': value,
                        'setting_type': setting_type,
                        'category': 'email',
                        'description': f'Configuração de email {key}'
                    }
                )
                if not created:
                    setting.value = value
                    setting.save()
            
            messages.success(request, 'Configurações de email salvas com sucesso!')
        
        return redirect('admin_panel:admin_settings_general')
    
    # Buscar configurações existentes
    try:
        settings_dict = {}
        settings = GlobalSetting.objects.filter(category__in=['general', 'email'])
        for setting in settings:
            settings_dict[setting.key] = setting.get_typed_value()
    except Exception:
        settings_dict = {}
    
    context = {
        'settings': settings_dict,
        'app_name': settings_dict.get('site_name', 'App Platform'),
        'base_url': settings_dict.get('base_url', 'http://localhost:8000'),
        'timezone': settings_dict.get('default_timezone', 'America/Sao_Paulo'),
        'default_language': settings_dict.get('default_language', 'pt-br'),
        'maintenance_mode': settings_dict.get('maintenance_mode', False),
        'from_email': settings_dict.get('from_email', 'noreply@appplatform.com'),
        'from_name': settings_dict.get('from_name', 'App Platform'),
    }
    
    return render(request, 'admin_panel/settings/general.html', context)


@login_required
def admin_settings_security(request):
    """Configurações de segurança do sistema"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    return render(request, 'admin_panel/settings/security.html')


@login_required
def admin_settings_notifications(request):
    """Configurações de notificações do sistema"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    return render(request, 'admin_panel/settings/notifications.html')


@login_required
def admin_settings_appearance(request):
    """Configurações de aparência do sistema"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    return render(request, 'admin_panel/settings/appearance.html')


class AccountForm(forms.ModelForm):
    """Formulário para criação e edição de contas"""
    owner = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        label='Proprietário',
        help_text='Selecione o usuário que será o proprietário desta conta',
        empty_label='Selecione um usuário'
    )
    
    class Meta:
        model = Account
        fields = ['name', 'email', 'cnpj', 'cpf', 'phone', 'address_line1', 'owner']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Nome da conta'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'email@exemplo.com'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': '00.000.000/0000-00'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': '000.000.000-00'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': '(11) 99999-9999'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'block w-full border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
                'placeholder': 'Rua, Avenida, etc.'
            }),
        }
        labels = {
            'name': 'Nome',
            'email': 'Email',
            'cnpj': 'CNPJ',
            'cpf': 'CPF',
            'phone': 'Telefone',
            'address_line1': 'Endereço',
            'owner': 'Proprietário',
        }


@login_required
def account_create(request):
    """Criar nova conta"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            # O proprietário já vem do formulário, não precisa definir aqui
            
            # Gerar slug único baseado no nome
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(account.name)
            if not base_slug:
                base_slug = 'account'
            
            # Verificar se o slug já existe e adicionar sufixo se necessário
            slug = base_slug
            counter = 1
            while Account.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            account.slug = slug
            account.save()
            
            # Criar membership para o proprietário (verificar se já existe)
            membership, created = AccountMembership.objects.get_or_create(
                account=account,
                user=account.owner,
                defaults={
                    'role': 'owner',
                    'status': 'active'
                }
            )
            
            messages.success(request, f'Conta "{account.name}" criada com sucesso!')
            return redirect('admin_panel:accounts_list')
        else:
            messages.error(request, 'Erro ao criar conta. Verifique os dados informados.')
    else:
        form = AccountForm()
    
    return render(request, 'admin_panel/accounts/form.html', {
        'form': form,
        'title': 'Nova Conta',
        'action': 'create'
    })


@login_required
def account_edit(request, account_id):
    """Editar conta existente"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    account = get_object_or_404(Account, id=account_id)
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'Conta "{account.name}" atualizada com sucesso!')
            return redirect('admin_panel:account_detail', account_id=account.id)
        else:
            messages.error(request, 'Erro ao atualizar conta. Verifique os dados informados.')
    else:
        form = AccountForm(instance=account)
    
    return render(request, 'admin_panel/accounts/form.html', {
        'form': form,
        'account': account,
        'title': f'Editar Conta: {account.name}',
        'action': 'edit'
    })


@login_required
def account_members(request, account_id):
    """Gerenciar membros da conta"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    account = get_object_or_404(Account, id=account_id)
    
    # Buscar membros com filtros
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    memberships = AccountMembership.objects.filter(account=account)
    
    if search_query:
        memberships = memberships.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__name__icontains=search_query)
        )
    
    if role_filter:
        memberships = memberships.filter(role=role_filter)
    
    if status_filter:
        if status_filter == 'active':
            memberships = memberships.filter(status='active')
        elif status_filter == 'inactive':
            memberships = memberships.filter(status='inactive')
    
    # Paginação
    paginator = Paginator(memberships.select_related('user'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_members = memberships.count()
    active_members = memberships.filter(status='active').count()
    owners = memberships.filter(role='owner').count()
    admins = memberships.filter(role='admin').count()
    
    return render(request, 'admin_panel/accounts/members.html', {
        'account': account,
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_members': total_members,
        'active_members': active_members,
        'owners': owners,
        'admins': admins,
        'role_choices': AccountMembership.ROLE_CHOICES,
    })


@login_required
@require_http_methods(["POST"])
def add_member(request, account_id):
    """Adicionar membro à conta"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    account = get_object_or_404(Account, id=account_id)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        role = data.get('role', 'member')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'ID do usuário é obrigatório'})
        
        user = get_object_or_404(User, id=user_id)
        
        # Verificar se o usuário já é membro da conta
        if AccountMembership.objects.filter(account=account, user=user).exists():
            return JsonResponse({'success': False, 'message': 'Usuário já é membro desta conta'})
        
        # Criar membership
        membership = AccountMembership.objects.create(
            account=account,
            user=user,
            role=role,
            status='active'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Usuário {user.username} adicionado como {membership.get_role_display()}',
            'membership': {
                'id': membership.id,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': membership.role,
                'role_display': membership.get_role_display(),
                'is_active': membership.status == 'active',
                'created_at': membership.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dados JSON inválidos'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def remove_member(request, account_id, membership_id):
    """Remover membro da conta"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    account = get_object_or_404(Account, id=account_id)
    membership = get_object_or_404(AccountMembership, id=membership_id, account=account)
    
    # Não permitir remover o proprietário
    if membership.role == 'owner':
        return JsonResponse({'success': False, 'message': 'Não é possível remover o proprietário da conta'})
    
    try:
        username = membership.user.username
        membership.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuário {username} removido da conta com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao remover membro: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def toggle_member_status(request, account_id, membership_id):
    """Alternar status do membro (ativo/inativo)"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    account = get_object_or_404(Account, id=account_id)
    membership = get_object_or_404(AccountMembership, id=membership_id, account=account)
    
    # Não permitir desativar o proprietário
    if membership.role == 'owner' and membership.status == 'active':
        return JsonResponse({'success': False, 'message': 'Não é possível desativar o proprietário da conta'})
    
    try:
        # Alternar entre active e inactive
        if membership.status == 'active':
            membership.status = 'inactive'
        else:
            membership.status = 'active'
        membership.save()
        
        status_text = 'ativado' if membership.status == 'active' else 'desativado'
        
        return JsonResponse({
            'success': True,
            'message': f'Membro {membership.user.username} {status_text} com sucesso',
            'is_active': membership.status == 'active'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao alterar status: {str(e)}'})


@login_required
def all_members(request):
    """Listar todas as contas com seus membros"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    # Filtros
    search_query = request.GET.get('search', '')
    account_filter = request.GET.get('account', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Buscar todas as contas com seus membros
    accounts = Account.objects.prefetch_related(
        'memberships__user'
    ).filter(status__in=['active', 'trial'])
    
    if account_filter:
        accounts = accounts.filter(id=account_filter)
    
    if search_query:
        accounts = accounts.filter(
            Q(name__icontains=search_query) |
            Q(memberships__user__username__icontains=search_query) |
            Q(memberships__user__email__icontains=search_query) |
            Q(memberships__user__name__icontains=search_query)
        ).distinct()
    
    # Coletar todas as memberships das contas filtradas
    all_memberships = []
    for account in accounts:
        memberships = account.memberships.select_related('user')
        
        if role_filter:
            memberships = memberships.filter(role=role_filter)
        
        if status_filter:
            if status_filter == 'active':
                memberships = memberships.filter(status='active')
            elif status_filter == 'inactive':
                memberships = memberships.filter(status='inactive')
        
        all_memberships.extend(list(memberships))
    
    # Paginação das memberships
    paginator = Paginator(all_memberships, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas gerais
    total_accounts = Account.objects.filter(status__in=['active', 'trial']).count()
    total_memberships = AccountMembership.objects.count()
    active_memberships = AccountMembership.objects.filter(status='active').count()
    
    # Opções para filtros
    all_accounts = Account.objects.filter(status__in=['active', 'trial']).values('id', 'name')
    role_choices = AccountMembership.ROLE_CHOICES
    
    context = {
        'memberships': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'account_filter': account_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'all_accounts': all_accounts,
        'role_choices': role_choices,
        'total_accounts': total_accounts,
        'total_memberships': total_memberships,
        'active_memberships': active_memberships,
        'title': 'Gerenciar Membros - Todas as Contas'
    }
    
    return render(request, 'admin_panel/members/all_members.html', context)


@login_required
def add_member_to_account(request):
    """Adicionar membro a uma conta específica"""
    if not request.user.is_staff:
        raise PermissionDenied('Você não tem permissão para acessar esta página.')
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        user_id = request.POST.get('user')
        role = request.POST.get('role', 'member')
        
        if not account_id or not user_id:
            messages.error(request, 'Conta e usuário são obrigatórios.')
            return redirect('admin_panel:add_member_to_account')
        
        try:
            account = Account.objects.get(id=account_id)
            user = User.objects.get(id=user_id)
            
            # Verificar se o usuário já é membro desta conta
            if AccountMembership.objects.filter(account=account, user=user).exists():
                messages.error(request, f'O usuário {user.username} já é membro da conta {account.name}.')
                return redirect('admin_panel:add_member_to_account')
            
            # Criar membership
            membership = AccountMembership.objects.create(
                account=account,
                user=user,
                role=role,
                status='active',
                invited_by=request.user
            )
            
            messages.success(request, f'Usuário {user.username} adicionado à conta {account.name} como {membership.get_role_display()}.')
            return redirect('admin_panel:all_members')
            
        except Account.DoesNotExist:
            messages.error(request, 'Conta não encontrada.')
        except User.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar membro: {str(e)}')
    
    # GET request - mostrar formulário
    accounts = Account.objects.filter(status__in=['active', 'trial']).values('id', 'name')
    users = User.objects.filter(is_active=True).values('id', 'username', 'email', 'first_name', 'last_name')
    role_choices = AccountMembership.ROLE_CHOICES
    
    context = {
        'accounts': accounts,
        'users': users,
        'role_choices': role_choices,
        'title': 'Adicionar Membro à Conta'
    }
    
    return render(request, 'admin_panel/members/add_member.html', context)
