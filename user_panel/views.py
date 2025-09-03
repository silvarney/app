from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import Account, AccountMembership
from users.models import User
from permissions.models import Permission, Role, UserRole


@login_required
def dashboard(request):
    """Dashboard principal do usuário"""
    user = request.user
    
    # Contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).annotate(
        member_count=Count('memberships')
    ).order_by('-created_at')
    
    # Estatísticas
    total_accounts = user_accounts.count()
    owned_accounts = user_accounts.filter(owner=user).count()
    member_accounts = total_accounts - owned_accounts
    
    # Atividade recente (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_memberships = AccountMembership.objects.filter(
        user=user,
        created_at__gte=thirty_days_ago
    ).select_related('account').order_by('-created_at')[:5]
    
    context = {
        'user_accounts': user_accounts[:5],  # Últimas 5 contas
        'total_accounts': total_accounts,
        'owned_accounts': owned_accounts,
        'member_accounts': member_accounts,
        'recent_memberships': recent_memberships,
    }
    
    return render(request, 'user_panel/dashboard.html', context)


@login_required
def accounts_list(request):
    """Lista todas as contas do usuário"""
    user = request.user
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Query base
    accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).annotate(
        member_count=Count('memberships'),
        user_role=models.Subquery(
            AccountMembership.objects.filter(
                account=models.OuterRef('pk'),
                user=user
            ).values('role')[:1]
        )
    ).distinct()
    
    # Filtros
    if search:
        accounts = accounts.filter(
            Q(name__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    if role_filter:
        accounts = accounts.filter(
            memberships__user=user,
            memberships__role=role_filter
        )
    
    accounts = accounts.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(accounts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Choices para filtros
    role_choices = AccountMembership.ROLE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role': role_filter,
        'role_choices': role_choices,
    }
    
    return render(request, 'user_panel/accounts/list.html', context)


@login_required
def account_detail(request, account_id):
    """Detalhes de uma conta específica"""
    user = request.user
    
    # Verificar se o usuário tem acesso à conta
    account = get_object_or_404(
        Account,
        id=account_id,
        memberships__user=user,
        memberships__status='active'
    )
    
    # Membership do usuário atual
    user_membership = AccountMembership.objects.get(
        account=account,
        user=user,
        status='active'
    )
    
    # Membros da conta
    memberships = AccountMembership.objects.filter(
        account=account,
        status='active'
    ).select_related('user').order_by('-created_at')
    
    # Convites pendentes (apenas para owners e admins)
    invites = []
    if user_membership.role in ['owner', 'admin']:
        # Aqui você implementaria a lógica de convites
        # invites = AccountInvite.objects.filter(account=account, status='pending')
        pass
    
    context = {
        'account': account,
        'user_membership': user_membership,
        'memberships': memberships,
        'invites': invites,
        'can_manage': user_membership.role in ['owner', 'admin'],
    }
    
    return render(request, 'user_panel/accounts/detail.html', context)


@login_required
def account_settings(request, account_id):
    """Configurações da conta"""
    user = request.user
    
    # Verificar se o usuário tem permissão para editar
    account = get_object_or_404(
        Account,
        id=account_id,
        memberships__user=user,
        memberships__role__in=['owner', 'admin'],
        memberships__status='active'
    )
    
    if request.method == 'POST':
        # Atualizar dados da conta
        account.name = request.POST.get('name', account.name)
        account.company_name = request.POST.get('company_name', account.company_name)
        account.save()
        
        messages.success(request, 'Configurações da conta atualizadas com sucesso!')
        return redirect('user_panel:account_detail', account_id=account.id)
    
    context = {
        'account': account,
    }
    
    return render(request, 'user_panel/accounts/settings.html', context)


@login_required
def profile_settings(request):
    """Configurações do perfil do usuário"""
    user = request.user
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        
        # Avatar
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        user.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('user_panel:profile_settings')
    
    context = {
        'user': user,
    }
    
    return render(request, 'user_panel/profile/settings.html', context)


@login_required
@require_http_methods(["POST"])
def leave_account(request, account_id):
    """Sair de uma conta (apenas para membros, não owners)"""
    user = request.user
    
    try:
        account = get_object_or_404(Account, id=account_id)
        membership = AccountMembership.objects.get(
            account=account,
            user=user,
            status='active'
        )
        
        # Owners não podem sair da própria conta
        if membership.role == 'owner':
            return JsonResponse({
                'success': False,
                'message': 'Proprietários não podem sair da própria conta.'
            })
        
        # Atualizar status do membership
        membership.status = 'inactive'
        membership.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Você saiu da conta "{account.name}" com sucesso.'
        })
        
    except AccountMembership.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Você não é membro desta conta.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Erro ao sair da conta.'
        })


@login_required
def switch_account(request, account_id):
    """Trocar conta ativa na sessão"""
    user = request.user
    
    try:
        account = get_object_or_404(
            Account,
            id=account_id,
            memberships__user=user,
            memberships__status='active'
        )
        
        # Salvar conta ativa na sessão
        request.session['active_account_id'] = account.id
        
        messages.success(request, f'Conta ativa alterada para "{account.name}".')
        
    except Account.DoesNotExist:
        messages.error(request, 'Conta não encontrada ou você não tem acesso.')
    
    return redirect('user_panel:dashboard')
