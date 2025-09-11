from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import Account, AccountMembership
from users.models import User, UserProfile
from site_management.models import Site, SiteBio
from site_management.forms import SiteBioForm
from django.http import HttpResponse
import csv
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Sum
from datetime import datetime
from collections import defaultdict
from permissions.models import Permission, Role, UserRole
from permissions.decorators import user_panel_required
from content.models import Content, Category, Tag
from site_management.models import Item, PlanType, TemplateCategory, SiteCategory, Service, SocialNetwork, CTA, BlogPost
from .forms import (
    SiteCategoryForm, ServiceForm, SocialNetworkForm, CTAForm, BlogPostForm
)
from site_management import views as site_views
from domains.models import Domain


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


@login_required
def notifications(request):
    """Lista de notificações do usuário"""
    user = request.user
    
    # Simulação de notificações (você pode implementar um modelo de Notification)
    notifications_data = []
    
    # Convites pendentes para contas
    # pending_invites = AccountInvite.objects.filter(email=user.email, status='pending')
    # for invite in pending_invites:
    #     notifications_data.append({
    #         'type': 'invite',
    #         'title': f'Convite para {invite.account.name}',
    #         'message': f'Você foi convidado para participar da conta {invite.account.name}',
    #         'created_at': invite.created_at,
    #         'action_url': f'/invites/{invite.id}/accept/',
    #     })
    
    # Mudanças de papel recentes
    recent_role_changes = AccountMembership.objects.filter(
        user=user,
        updated_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('account').order_by('-updated_at')
    
    for membership in recent_role_changes:
        notifications_data.append({
            'type': 'role_change',
            'title': f'Papel alterado em {membership.account.name}',
            'message': f'Seu papel foi alterado para {membership.get_role_display()}',
            'created_at': membership.updated_at,
            'action_url': f'/accounts/{membership.account.id}/',
        })
    
    # Ordenar por data
    notifications_data.sort(key=lambda x: x['created_at'], reverse=True)
    
    context = {
        'notifications': notifications_data[:20],  # Últimas 20 notificações
    }
    
    return render(request, 'user_panel/notifications.html', context)


@login_required
def activity_log(request):
    """Log de atividades do usuário"""
    user = request.user
    
    # Atividades recentes
    activities = []
    
    # Contas criadas
    owned_accounts = Account.objects.filter(owner=user).order_by('-created_at')[:10]
    for account in owned_accounts:
        activities.append({
            'type': 'account_created',
            'title': 'Conta criada',
            'description': f'Você criou a conta "{account.name}"',
            'timestamp': account.created_at,
            'icon': 'fas fa-plus-circle',
            'color': 'green'
        })
    
    # Participações em contas
    memberships = AccountMembership.objects.filter(
        user=user,
        status='active'
    ).exclude(
        account__owner=user
    ).select_related('account').order_by('-created_at')[:10]
    
    for membership in memberships:
        activities.append({
            'type': 'account_joined',
            'title': 'Ingressou em conta',
            'description': f'Você ingressou na conta "{membership.account.name}" como {membership.get_role_display()}',
            'timestamp': membership.created_at,
            'icon': 'fas fa-user-plus',
            'color': 'blue'
        })
    
    # Ordenar por timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'activities': activities[:50],  # Últimas 50 atividades
    }
    
    return render(request, 'user_panel/activity.html', context)


@login_required
def user_analytics(request):
    """Analytics pessoais do usuário"""
    user = request.user
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Estatísticas de contas
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    owned_accounts = user_accounts.filter(owner=user)
    member_accounts = user_accounts.exclude(owner=user)
    
    # Crescimento de participação em contas ao longo do tempo
    membership_growth = []
    current_date = start_date
    while current_date <= timezone.now():
        count = AccountMembership.objects.filter(
            user=user,
            created_at__lte=current_date,
            status='active'
        ).count()
        
        membership_growth.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count
        })
        
        current_date += timedelta(days=1)
    
    # Distribuição por papéis
    role_distribution = AccountMembership.objects.filter(
        user=user,
        status='active'
    ).values('role').annotate(count=Count('id')).order_by('-count')
    
    # Contas mais ativas (por número de membros)
    top_accounts = user_accounts.annotate(
        member_count=Count('memberships')
    ).order_by('-member_count')[:10]
    
    context = {
        'days': days,
        'total_accounts': user_accounts.count(),
        'owned_accounts_count': owned_accounts.count(),
        'member_accounts_count': member_accounts.count(),
        'membership_growth': json.dumps(membership_growth),
        'role_distribution': role_distribution,
        'top_accounts': top_accounts,
    }
    
    return render(request, 'user_panel/analytics.html', context)


@login_required
def export_data(request):
    """Exportar dados do usuário em CSV"""
    user = request.user
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="user_data_{user.id}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Cabeçalho
    writer.writerow([
        'Account Name', 'Company Name', 'Role', 'Status', 
        'Member Count', 'Joined Date', 'Account Created'
    ])
    
    # Dados das contas
    memberships = AccountMembership.objects.filter(
        user=user
    ).select_related('account').annotate(
        member_count=Count('account__memberships')
    ).order_by('-created_at')
    
    for membership in memberships:
        writer.writerow([
            membership.account.name,
            membership.account.company_name or '',
            membership.get_role_display(),
            membership.get_status_display(),
            membership.member_count,
            membership.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            membership.account.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response


# ===== VIEWS DE GERENCIAMENTO DE ITENS =====

@login_required
def items_list(request):
    """Lista todos os itens disponíveis para planos"""
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # Query base
    items = Item.objects.all()
    
    # Aplicar filtros
    if search:
        items = items.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status:
        if status == 'active':
            items = items.filter(is_active=True)
        elif status == 'inactive':
            items = items.filter(is_active=False)
    
    # Ordenação
    items = items.order_by('title')
    
    # Paginação
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_items = Item.objects.count()
    active_items = Item.objects.filter(is_active=True).count()
    inactive_items = total_items - active_items
    
    context = {
        'page_title': 'Gerenciar Itens',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_items': total_items,
        'active_items': active_items,
        'inactive_items': inactive_items,
    }
    return render(request, 'user_panel/items/list.html', context)


@login_required
def items_create(request):
    """Criar novo item"""
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        value = request.POST.get('value', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validações
        errors = []
        
        if not title:
            errors.append('O título é obrigatório.')
        elif len(title) > 200:
            errors.append('O título deve ter no máximo 200 caracteres.')
        
        if not description:
            errors.append('A descrição é obrigatória.')
        
        if not value:
            errors.append('O valor é obrigatório.')
        else:
            try:
                value_decimal = float(value.replace(',', '.'))
                if value_decimal < 0:
                    errors.append('O valor deve ser positivo.')
            except ValueError:
                errors.append('Valor inválido.')
        
        # Verificar se já existe item com mesmo título
        if title and Item.objects.filter(title__iexact=title).exists():
            errors.append('Já existe um item com este título.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Criar item
            item = Item.objects.create(
                title=title,
                description=description,
                value=value_decimal,
                is_active=is_active
            )
            
            messages.success(request, f'Item "{item.title}" criado com sucesso!')
            return redirect('user_panel:items_list')
    
    context = {
        'page_title': 'Criar Item'
    }
    return render(request, 'user_panel/items/create.html', context)


@login_required
def items_edit(request, item_id):
    """Editar item existente"""
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        value = request.POST.get('value', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validações
        errors = []
        
        if not title:
            errors.append('O título é obrigatório.')
        elif len(title) > 200:
            errors.append('O título deve ter no máximo 200 caracteres.')
        
        if not description:
            errors.append('A descrição é obrigatória.')
        
        if not value:
            errors.append('O valor é obrigatório.')
        else:
            try:
                value_decimal = float(value.replace(',', '.'))
                if value_decimal < 0:
                    errors.append('O valor deve ser positivo.')
            except ValueError:
                errors.append('Valor inválido.')
        
        # Verificar se já existe item com mesmo título (exceto o atual)
        if title and Item.objects.filter(title__iexact=title).exclude(id=item.id).exists():
            errors.append('Já existe um item com este título.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Atualizar item
            item.title = title
            item.description = description
            item.value = value_decimal
            item.is_active = is_active
            item.save()
            
            messages.success(request, f'Item "{item.title}" atualizado com sucesso!')
            return redirect('user_panel:items_list')
    
    context = {
        'page_title': 'Editar Item',
        'item': item
    }
    return render(request, 'user_panel/items/edit.html', context)


@login_required
def items_delete(request, item_id):
    """Excluir item"""
    
    item = get_object_or_404(Item, id=item_id)
    
    # Verificar se o item está sendo usado em algum plano
    plan_types_using = PlanType.objects.filter(items=item)
    
    if request.method == 'POST':
        if plan_types_using.exists():
            messages.error(request, f'Não é possível excluir o item "{item.title}" pois ele está sendo usado em {plan_types_using.count()} tipo(s) de plano.')
            return redirect('user_panel:items_list')
        
        item_title = item.title
        item.delete()
        messages.success(request, f'Item "{item_title}" excluído com sucesso!')
        return redirect('user_panel:items_list')
    
    context = {
        'page_title': 'Excluir Item',
        'item': item,
        'plan_types_using': plan_types_using
    }
    return render(request, 'user_panel/items/delete.html', context)


# ===== VIEWS DE RELATÓRIOS =====

@user_panel_required
def reports_dashboard(request):
    """Dashboard principal de relatórios"""
    user = request.user
    
    # Estatísticas gerais
    total_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct().count()
    
    total_members = AccountMembership.objects.filter(
        account__memberships__user=user,
        account__memberships__status='active'
    ).distinct().count()
    
    # Atividade dos últimos 30 dias
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_activity = AccountMembership.objects.filter(
        account__memberships__user=user,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Contas mais ativas
    active_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).annotate(
        member_count=Count('memberships')
    ).order_by('-member_count')[:5]
    
    context = {
        'total_accounts': total_accounts,
        'total_members': total_members,
        'recent_activity': recent_activity,
        'active_accounts': active_accounts,
        'page_title': 'Dashboard de Relatórios'
    }
    
    return render(request, 'user_panel/reports/dashboard.html', context)


@user_panel_required
def reports_accounts(request):
    """Relatório detalhado de contas"""
    user = request.user
    
    # Filtros
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Query base
    accounts = Account.objects.filter(
        memberships__user=user
    ).annotate(
        member_count=Count('memberships'),
        active_members=Count('memberships', filter=Q(memberships__status='active'))
    ).distinct()
    
    # Aplicar filtros
    if status:
        if status == 'active':
            accounts = accounts.filter(memberships__status='active')
        elif status == 'inactive':
            accounts = accounts.filter(memberships__status='inactive')
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            accounts = accounts.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            accounts = accounts.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    # Ordenação
    accounts = accounts.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'page_title': 'Relatório de Contas'
    }
    
    return render(request, 'user_panel/reports/accounts.html', context)


@user_panel_required
def reports_members(request):
    """Relatório detalhado de membros"""
    user = request.user
    
    # Filtros
    status = request.GET.get('status', '')
    role = request.GET.get('role', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Query base
    memberships = AccountMembership.objects.filter(
        account__memberships__user=user
    ).select_related('user', 'account').distinct()
    
    # Aplicar filtros
    if status:
        memberships = memberships.filter(status=status)
    
    if role:
        memberships = memberships.filter(role=role)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            memberships = memberships.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            memberships = memberships.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    # Ordenação
    memberships = memberships.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(memberships, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_members = memberships.count()
    active_members = memberships.filter(status='active').count()
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'role': role,
        'date_from': date_from,
        'date_to': date_to,
        'total_members': total_members,
        'active_members': active_members,
        'page_title': 'Relatório de Membros'
    }
    
    return render(request, 'user_panel/reports/members.html', context)


@user_panel_required
def reports_activity(request):
    """Relatório de atividades"""
    user = request.user
    
    # Filtros
    period = request.GET.get('period', '30')
    
    # Calcular período
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Atividades recentes
    recent_memberships = AccountMembership.objects.filter(
        account__memberships__user=user,
        created_at__gte=start_date
    ).select_related('user', 'account').order_by('-created_at')
    
    # Estatísticas por dia
    daily_stats = defaultdict(int)
    for membership in recent_memberships:
        day = membership.created_at.date()
        daily_stats[day] += 1
    
    # Converter para lista ordenada
    daily_data = []
    current_date = start_date.date()
    end_date = timezone.now().date()
    
    while current_date <= end_date:
        daily_data.append({
            'date': current_date,
            'count': daily_stats.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    # Paginação das atividades
    paginator = Paginator(recent_memberships, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'period': period,
        'daily_data': daily_data,
        'total_activities': recent_memberships.count(),
        'page_title': 'Relatório de Atividades'
    }
    
    return render(request, 'user_panel/reports/activity.html', context)


@user_panel_required
def reports_export(request):
    """Exportar relatórios em CSV"""
    user = request.user
    export_type = request.GET.get('type', 'accounts')
    
    if export_type == 'accounts':
        # Exportar contas
        accounts = Account.objects.filter(
            memberships__user=user
        ).annotate(
            member_count=Count('memberships')
        ).distinct()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contas.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nome', 'Descrição', 'Membros', 'Criado em', 'Status'])
        
        for account in accounts:
            writer.writerow([
                account.name,
                account.description or '',
                account.member_count,
                account.created_at.strftime('%d/%m/%Y %H:%M'),
                'Ativa' if account.is_active else 'Inativa'
            ])
    
    elif export_type == 'members':
        # Exportar membros
        memberships = AccountMembership.objects.filter(
            account__memberships__user=user
        ).select_related('user', 'account').distinct()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="membros.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nome', 'Email', 'Conta', 'Função', 'Status', 'Adicionado em'])
        
        for membership in memberships:
            writer.writerow([
                membership.user.get_full_name() or membership.user.username,
                membership.user.email,
                membership.account.name,
                membership.get_role_display(),
                membership.get_status_display(),
                membership.created_at.strftime('%d/%m/%Y %H:%M')
            ])
    
    else:
        # Tipo inválido, redirecionar
        messages.error(request, 'Tipo de exportação inválido.')
        return redirect('user_panel:reports_dashboard')
    
    return response


# ===== VIEWS DE GERENCIAMENTO DE TIPOS DE PLANOS =====

@login_required
def plan_types_list(request):
    """Lista todos os tipos de planos disponíveis"""
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    template_category = request.GET.get('template_category', '')
    
    # Query base
    plan_types = PlanType.objects.select_related('template_category').prefetch_related('items')
    
    # Aplicar filtros
    if search:
        plan_types = plan_types.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status:
        if status == 'active':
            plan_types = plan_types.filter(is_active=True)
        elif status == 'inactive':
            plan_types = plan_types.filter(is_active=False)
    
    if template_category:
        plan_types = plan_types.filter(template_category_id=template_category)
    
    # Ordenação
    plan_types = plan_types.order_by('title')
    
    # Paginação
    paginator = Paginator(plan_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_plan_types = PlanType.objects.count()
    active_plan_types = PlanType.objects.filter(is_active=True).count()
    inactive_plan_types = total_plan_types - active_plan_types
    
    # Categorias para filtro
    template_categories = TemplateCategory.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'template_category': template_category,
        'total_plan_types': total_plan_types,
        'active_plan_types': active_plan_types,
        'inactive_plan_types': inactive_plan_types,
        'template_categories': template_categories,
        'page_title': 'Tipos de Planos'
    }
    
    return render(request, 'user_panel/plan_types/list.html', context)


@login_required
def plan_types_create(request):
    """Criar um novo tipo de plano"""
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount = request.POST.get('discount', '0')
        template_category_id = request.POST.get('template_category')
        is_active = request.POST.get('is_active') == 'on'
        selected_items = request.POST.getlist('items')
        
        # Validações
        errors = {}
        
        if not title:
            errors['title'] = 'O título é obrigatório'
        elif PlanType.objects.filter(title=title).exists():
            errors['title'] = 'Já existe um tipo de plano com este título'
        
        if not description:
            errors['description'] = 'A descrição é obrigatória'
        
        try:
            discount = float(discount)
            if discount < 0 or discount > 100:
                errors['discount'] = 'O desconto deve estar entre 0 e 100%'
        except ValueError:
            errors['discount'] = 'Desconto inválido'
        
        if not template_category_id:
            errors['template_category'] = 'A categoria de template é obrigatória'
        else:
            try:
                template_category = TemplateCategory.objects.get(id=template_category_id)
            except TemplateCategory.DoesNotExist:
                errors['template_category'] = 'Categoria de template inválida'
        
        if not selected_items:
            errors['items'] = 'Selecione pelo menos um item para o plano'
        
        if not errors:
            # Criar o tipo de plano
            plan_type = PlanType.objects.create(
                title=title,
                description=description,
                discount=discount,
                template_category=template_category,
                is_active=is_active
            )
            
            # Adicionar itens
            items = Item.objects.filter(id__in=selected_items)
            plan_type.items.set(items)
            
            messages.success(request, f'Tipo de plano "{title}" criado com sucesso!')
            return redirect('user_panel:plan_types_list')
        else:
            for field, error in errors.items():
                messages.error(request, error)
    
    # Buscar dados para o formulário
    template_categories = TemplateCategory.objects.all().order_by('name')
    items = Item.objects.filter(is_active=True).order_by('title')
    
    context = {
        'template_categories': template_categories,
        'items': items,
        'page_title': 'Criar Tipo de Plano'
    }
    
    return render(request, 'user_panel/plan_types/create.html', context)


@login_required
def plan_types_edit(request, plan_type_id):
    """Editar um tipo de plano existente"""
    
    plan_type = get_object_or_404(PlanType, id=plan_type_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        discount = request.POST.get('discount', '0')
        template_category_id = request.POST.get('template_category')
        is_active = request.POST.get('is_active') == 'on'
        selected_items = request.POST.getlist('items')
        
        # Validações
        errors = {}
        
        if not title:
            errors['title'] = 'O título é obrigatório'
        elif PlanType.objects.filter(title=title).exclude(id=plan_type.id).exists():
            errors['title'] = 'Já existe um tipo de plano com este título'
        
        if not description:
            errors['description'] = 'A descrição é obrigatória'
        
        try:
            discount = float(discount)
            if discount < 0 or discount > 100:
                errors['discount'] = 'O desconto deve estar entre 0 e 100%'
        except ValueError:
            errors['discount'] = 'Desconto inválido'
        
        if not template_category_id:
            errors['template_category'] = 'A categoria de template é obrigatória'
        else:
            try:
                template_category = TemplateCategory.objects.get(id=template_category_id)
            except TemplateCategory.DoesNotExist:
                errors['template_category'] = 'Categoria de template inválida'
        
        if not selected_items:
            errors['items'] = 'Selecione pelo menos um item para o plano'
        
        if not errors:
            # Atualizar o tipo de plano
            plan_type.title = title
            plan_type.description = description
            plan_type.discount = discount
            plan_type.template_category = template_category
            plan_type.is_active = is_active
            plan_type.save()
            
            # Atualizar itens
            items = Item.objects.filter(id__in=selected_items)
            plan_type.items.set(items)
            
            messages.success(request, f'Tipo de plano "{title}" atualizado com sucesso!')
            return redirect('user_panel:plan_types_list')
        else:
            for field, error in errors.items():
                messages.error(request, error)
    
    # Buscar dados para o formulário
    template_categories = TemplateCategory.objects.all().order_by('name')
    items = Item.objects.filter(is_active=True).order_by('title')
    
    context = {
        'plan_type': plan_type,
        'template_categories': template_categories,
        'items': items,
        'page_title': f'Editar Tipo de Plano - {plan_type.title}'
    }
    
    return render(request, 'user_panel/plan_types/edit.html', context)


@login_required
def plan_types_delete(request, plan_type_id):
    """Excluir um tipo de plano"""
    
    plan_type = get_object_or_404(PlanType, id=plan_type_id)
    
    if request.method == 'POST':
        confirm_title = request.POST.get('confirm_title', '').strip()
        confirm_deletion = request.POST.get('confirm_deletion')
        
        if confirm_title == plan_type.title and confirm_deletion:
            title = plan_type.title
            plan_type.delete()
            messages.success(request, f'Tipo de plano "{title}" excluído com sucesso!')
            return redirect('user_panel:plan_types_list')
        else:
            messages.error(request, 'Confirmação inválida. Verifique o título digitado e marque a confirmação.')
    
    context = {
        'plan_type': plan_type,
        'page_title': f'Excluir Tipo de Plano - {plan_type.title}'
    }
    
    return render(request, 'user_panel/plan_types/delete.html', context)


# ===== VIEWS DE ITENS DA ASSINATURA =====

@login_required
def subscription_items_list(request):
    """Lista todos os itens da assinatura"""
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # Query base - usando Item model que já existe
    items = Item.objects.all()
    
    # Aplicar filtros
    if search:
        items = items.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status:
        if status == 'active':
            items = items.filter(is_active=True)
        elif status == 'inactive':
            items = items.filter(is_active=False)
    
    # Ordenação
    items = items.order_by('title')
    
    # Paginação
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_items = Item.objects.count()
    active_items = Item.objects.filter(is_active=True).count()
    inactive_items = total_items - active_items
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_items': total_items,
        'active_items': active_items,
        'inactive_items': inactive_items,
        'page_title': 'Itens da Assinatura'
    }
    return render(request, 'user_panel/subscription_items/list.html', context)


@login_required
def subscription_items_create(request):
    """Criar novo item da assinatura"""
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        value = request.POST.get('value', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validações
        errors = []
        
        if not title:
            errors.append('O título é obrigatório.')
        elif len(title) > 200:
            errors.append('O título deve ter no máximo 200 caracteres.')
        
        if not description:
            errors.append('A descrição é obrigatória.')
        
        if not value:
            errors.append('O valor é obrigatório.')
        else:
            try:
                value_decimal = float(value.replace(',', '.'))
                if value_decimal < 0:
                    errors.append('O valor deve ser positivo.')
            except ValueError:
                errors.append('Valor inválido.')
        
        # Verificar se já existe item com mesmo título
        if title and Item.objects.filter(title__iexact=title).exists():
            errors.append('Já existe um item com este título.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Criar item
            item = Item.objects.create(
                title=title,
                description=description,
                value=value_decimal,
                is_active=is_active
            )
            
            messages.success(request, f'Item "{item.title}" criado com sucesso!')
            return redirect('user_panel:subscription_items_list')
    
    context = {
        'page_title': 'Criar Item da Assinatura'
    }
    return render(request, 'user_panel/subscription_items/create.html', context)


@login_required
def subscription_items_edit(request, item_id):
    """Editar item da assinatura existente"""
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        value = request.POST.get('value', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validações
        errors = []
        
        if not title:
            errors.append('O título é obrigatório.')
        elif len(title) > 200:
            errors.append('O título deve ter no máximo 200 caracteres.')
        
        if not description:
            errors.append('A descrição é obrigatória.')
        
        if not value:
            errors.append('O valor é obrigatório.')
        else:
            try:
                value_decimal = float(value.replace(',', '.'))
                if value_decimal < 0:
                    errors.append('O valor deve ser positivo.')
            except ValueError:
                errors.append('Valor inválido.')
        
        # Verificar se já existe item com mesmo título (exceto o atual)
        if title and Item.objects.filter(title__iexact=title).exclude(id=item.id).exists():
            errors.append('Já existe um item com este título.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Atualizar item
            item.title = title
            item.description = description
            item.value = value_decimal
            item.is_active = is_active
            item.save()
            
            messages.success(request, f'Item "{item.title}" atualizado com sucesso!')
            return redirect('user_panel:subscription_items_list')
    
    context = {
        'item': item,
        'page_title': f'Editar Item - {item.title}'
    }
    return render(request, 'user_panel/subscription_items/edit.html', context)


@login_required
def subscription_items_delete(request, item_id):
    """Excluir item da assinatura"""
    
    item = get_object_or_404(Item, id=item_id)
    
    # Verificar se o item está sendo usado em algum plano
    plan_types_using = PlanType.objects.filter(items=item)
    
    if request.method == 'POST':
        if plan_types_using.exists():
            messages.error(request, f'Não é possível excluir o item "{item.title}" pois ele está sendo usado em {plan_types_using.count()} tipo(s) de plano.')
            return redirect('user_panel:subscription_items_list')
        
        item_title = item.title
        item.delete()
        messages.success(request, f'Item "{item_title}" excluído com sucesso!')
        return redirect('user_panel:subscription_items_list')
    
    context = {
        'item': item,
        'plan_types_using': plan_types_using,
        'page_title': f'Excluir Item - {item.title}'
    }
    return render(request, 'user_panel/subscription_items/delete.html', context)


# ===== VIEWS DE EXTRATOS =====

@login_required
def extracts_list(request):
    """Lista todos os extratos"""
    user = request.user
    
    # Filtros
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Por enquanto, vamos simular extratos baseados nas contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    # Simular dados de extrato
    extracts_data = []
    for account in user_accounts:
        # Simular algumas transações para cada conta
        for i in range(5):
            extracts_data.append({
                'id': f'{account.id}_{i}',
                'account': account,
                'description': f'Transação {i+1} - {account.name}',
                'amount': 100.00 * (i + 1),
                'type': 'credit' if i % 2 == 0 else 'debit',
                'date': timezone.now() - timedelta(days=i*7),
                'status': 'completed'
            })
    
    # Aplicar filtros
    if search:
        extracts_data = [e for e in extracts_data if search.lower() in e['description'].lower()]
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            extracts_data = [e for e in extracts_data if e['date'].date() >= date_from_parsed]
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            extracts_data = [e for e in extracts_data if e['date'].date() <= date_to_parsed]
        except ValueError:
            pass
    
    # Ordenar por data
    extracts_data.sort(key=lambda x: x['date'], reverse=True)
    
    # Paginação
    paginator = Paginator(extracts_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_credit = sum(e['amount'] for e in extracts_data if e['type'] == 'credit')
    total_debit = sum(e['amount'] for e in extracts_data if e['type'] == 'debit')
    balance = total_credit - total_debit
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'balance': balance,
        'page_title': 'Extratos'
    }
    
    return render(request, 'user_panel/extracts/list.html', context)


@login_required
def extract_detail(request, extract_id):
    """Exibe detalhes de um extrato específico"""
    # Por enquanto, simular detalhes do extrato
    try:
        account_id, transaction_id = extract_id.split('_')
        account = get_object_or_404(Account, id=account_id)
        
        # Simular dados do extrato
        extract_data = {
            'id': extract_id,
            'account': account,
            'description': f'Transação {transaction_id} - {account.name}',
            'amount': 100.00 * int(transaction_id),
            'type': 'credit' if int(transaction_id) % 2 == 0 else 'debit',
            'date': timezone.now() - timedelta(days=int(transaction_id)*7),
            'status': 'completed',
            'reference': f'REF{extract_id.upper()}',
            'details': f'Detalhes da transação {transaction_id} para a conta {account.name}'
        }
        
        context = {
            'extract': extract_data,
            'page_title': f'Extrato - {extract_data["reference"]}'
        }
        
        return render(request, 'user_panel/extracts/detail.html', context)
        
    except (ValueError, Account.DoesNotExist):
        messages.error(request, 'Extrato não encontrado.')
        return redirect('user_panel:extracts_list')


@login_required
def extracts_export(request):
    """Exportar extratos em CSV"""
    user = request.user
    
    # Buscar dados para exportação (simulados)
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="extratos_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Cabeçalho
    writer.writerow([
        'Data', 'Conta', 'Descrição', 'Tipo', 'Valor', 'Status', 'Referência'
    ])
    
    # Dados simulados
    for account in user_accounts:
        for i in range(10):
            writer.writerow([
                (timezone.now() - timedelta(days=i*3)).strftime('%d/%m/%Y %H:%M'),
                account.name,
                f'Transação {i+1} - {account.name}',
                'Crédito' if i % 2 == 0 else 'Débito',
                f'R$ {100.00 * (i + 1):.2f}',
                'Concluída',
                f'REF{account.id}_{i}'
            ])
    
    return response


@user_panel_required
def settings(request):
    """Página de configurações do usuário"""
    user = request.user
    
    # Garantir que o usuário tenha um perfil
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Verificar se o usuário tem permissão para gerenciar configurações da conta
    can_manage_account = False
    account_membership = None
    
    # Buscar membership ativo do usuário
    try:
        account_membership = AccountMembership.objects.filter(
            user=user,
            status='active'
        ).select_related('account').first()
        
        if account_membership:
            can_manage_account = account_membership.role in ['owner', 'admin']
    except Exception:
        pass
    
    if request.method == 'POST':
        from django.contrib import messages
        
        try:
            # Atualizar configurações pessoais
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.dark_theme = request.POST.get('dark_theme') == 'on'
            profile.language = request.POST.get('language', 'pt-BR')
            profile.save()
            
            messages.success(request, 'Configurações salvas com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao salvar configurações: {str(e)}')
        
        return redirect('user_panel:settings')
    
    context = {
        'user': user,
        'can_manage_account': can_manage_account,
        'is_admin': user.is_staff,
        'account_membership': account_membership,
    }
    
    return render(request, 'user_panel/settings.html', context)


@user_panel_required
def members_list(request):
    """Lista todos os membros das contas do usuário"""
    user = request.user
    
    # Buscar todas as contas onde o usuário é membro
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    # Se o usuário tem uma conta ativa, mostrar membros dessa conta
    current_account = getattr(user, 'current_account', None)
    if not current_account and user_accounts.exists():
        current_account = user_accounts.first()
    
    members = []
    can_manage = False
    
    if current_account:
        # Verificar se pode gerenciar membros
        try:
            user_membership = AccountMembership.objects.get(
                account=current_account,
                user=user,
                status='active'
            )
            can_manage = user_membership.role in ['owner', 'admin']
        except AccountMembership.DoesNotExist:
            pass
        
        # Buscar todos os membros da conta atual
        members = AccountMembership.objects.filter(
            account=current_account,
            status='active'
        ).select_related('user').order_by('-created_at')
    
    return render(request, 'user_panel/members/list.html', {
        'members': members,
        'current_account': current_account,
        'user_accounts': user_accounts,
        'can_manage': can_manage,
    })


@user_panel_required
def invite_member(request):
    """Convidar novo membro para a conta"""
    user = request.user
    
    # Buscar conta ativa do usuário
    current_account = None
    try:
        user_membership = AccountMembership.objects.filter(
            user=user,
            status='active'
        ).select_related('account').first()
        
        if user_membership:
            current_account = user_membership.account
    except Exception:
        pass
    
    if not current_account:
        messages.error(request, 'Você precisa estar em uma conta para convidar membros.')
        return redirect('user_panel:members_list')
    
    # Verificar se o usuário pode convidar membros
    try:
        user_membership = AccountMembership.objects.get(
            account=current_account,
            user=user,
            status='active'
        )
        if user_membership.role not in ['owner', 'admin']:
            messages.error(request, 'Você não tem permissão para convidar membros.')
            return redirect('user_panel:members_list')
    except AccountMembership.DoesNotExist:
        messages.error(request, 'Você não tem permissão para convidar membros.')
        return redirect('user_panel:members_list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role', 'member')
        
        if not email:
            messages.error(request, 'Email é obrigatório.')
        else:
            try:
                # Verificar se o usuário já existe
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    invited_user = User.objects.get(email=email)
                    
                    # Verificar se já é membro
                    existing_membership = AccountMembership.objects.filter(
                        account=current_account,
                        user=invited_user
                    ).first()
                    
                    if existing_membership:
                        if existing_membership.status == 'active':
                            messages.error(request, 'Este usuário já é membro da conta.')
                        else:
                            # Reativar membership
                            existing_membership.status = 'active'
                            existing_membership.role = role
                            existing_membership.save()
                            messages.success(request, f'Usuário {email} foi reativado como membro.')
                    else:
                        # Criar novo membership
                        AccountMembership.objects.create(
                            account=current_account,
                            user=invited_user,
                            role=role,
                            status='active'
                        )
                        messages.success(request, f'Usuário {email} foi adicionado como membro.')
                        
                except User.DoesNotExist:
                    messages.error(request, 'Usuário com este email não foi encontrado. O usuário precisa se cadastrar primeiro.')
                    
            except Exception as e:
                messages.error(request, f'Erro ao convidar membro: {str(e)}')
        
        return redirect('user_panel:members_list')
    
    return render(request, 'user_panel/members/invite.html', {
        'current_account': current_account,
        'role_choices': AccountMembership.ROLE_CHOICES,
    })


@user_panel_required
def edit_member(request, membership_id):
    """Editar papel de um membro"""
    user = request.user
    
    try:
        membership = AccountMembership.objects.get(
            id=membership_id,
            status='active'
        )
    except AccountMembership.DoesNotExist:
        messages.error(request, 'Membro não encontrado.')
        return redirect('user_panel:members_list')
    
    # Verificar permissões
    try:
        user_membership = AccountMembership.objects.get(
            account=membership.account,
            user=user,
            status='active'
        )
        if user_membership.role not in ['owner', 'admin']:
            messages.error(request, 'Você não tem permissão para editar membros.')
            return redirect('user_panel:members_list')
    except AccountMembership.DoesNotExist:
        messages.error(request, 'Você não tem permissão para editar membros.')
        return redirect('user_panel:members_list')
    
    # Não permitir editar o owner
    if membership.role == 'owner':
        messages.error(request, 'Não é possível editar o proprietário da conta.')
        return redirect('user_panel:members_list')
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        
        if new_role in dict(AccountMembership.ROLE_CHOICES):
            # Não permitir que admin se promova a owner
            if new_role == 'owner' and user_membership.role != 'owner':
                messages.error(request, 'Apenas o proprietário pode definir outro proprietário.')
            else:
                membership.role = new_role
                membership.save()
                messages.success(request, f'Papel do membro {membership.user.get_full_name() or membership.user.email} foi atualizado.')
        else:
            messages.error(request, 'Papel inválido.')
        
        return redirect('user_panel:members_list')
    
    return render(request, 'user_panel/members/edit.html', {
        'membership': membership,
        'role_choices': AccountMembership.ROLE_CHOICES,
    })


@user_panel_required
def remove_member(request, membership_id):
    """Remover membro da conta"""
    user = request.user
    
    try:
        membership = AccountMembership.objects.get(
            id=membership_id,
            status='active'
        )
    except AccountMembership.DoesNotExist:
        messages.error(request, 'Membro não encontrado.')
        return redirect('user_panel:members_list')
    
    # Verificar permissões
    try:
        user_membership = AccountMembership.objects.get(
            account=membership.account,
            user=user,
            status='active'
        )
        if user_membership.role not in ['owner', 'admin']:
            messages.error(request, 'Você não tem permissão para remover membros.')
            return redirect('user_panel:members_list')
    except AccountMembership.DoesNotExist:
        messages.error(request, 'Você não tem permissão para remover membros.')
        return redirect('user_panel:members_list')
    
    # Não permitir remover o owner
    if membership.role == 'owner':
        messages.error(request, 'Não é possível remover o proprietário da conta.')
        return redirect('user_panel:members_list')
    
    # Não permitir que o usuário remova a si mesmo
    if membership.user == user:
        messages.error(request, 'Você não pode remover a si mesmo. Use a opção "Sair da conta".')
        return redirect('user_panel:members_list')
    
    if request.method == 'POST':
        member_name = membership.user.get_full_name() or membership.user.email
        membership.status = 'inactive'
        membership.save()
        
        messages.success(request, f'Membro {member_name} foi removido da conta.')
        return redirect('user_panel:members_list')
    
    return render(request, 'user_panel/members/remove.html', {
        'membership': membership,
    })


# Bio Views
@login_required
def bio_list(request):
    """Lista de bios do usuário"""
    # Buscar sites do usuário
    user_sites = Site.objects.filter(
        account__memberships__user=request.user,
        account__memberships__status='active',
        status='active'
    ).distinct()
    
    # Buscar bios dos sites do usuário
    bios = SiteBio.objects.filter(site__in=user_sites).select_related('site')
    
    # Paginação
    paginator = Paginator(bios, 10)
    page = request.GET.get('page')
    bios = paginator.get_page(page)
    
    context = {
        'title': 'Bio',
        'breadcrumb': 'Bio',
        'bios': bios,
        'user_sites': user_sites
    }
    return render(request, 'user_panel/bio/list.html', context)

@login_required
def bio_create(request):
    """Criar nova bio"""
    if request.method == 'POST':
        form = SiteBioForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Verificar se o usuário tem permissão no site selecionado
            site = form.cleaned_data['site']
            user_has_permission = AccountMembership.objects.filter(
                user=request.user,
                account=site.account,
                status='active',
                role__in=['owner', 'admin']
            ).exists()
            
            if not user_has_permission:
                messages.error(request, 'Você não tem permissão para criar bio neste site.')
                return redirect('user_panel:bio_create')
            
            # Verificar se já existe bio para este site
            if SiteBio.objects.filter(site=site).exists():
                messages.error(request, 'Este site já possui uma bio. Edite a bio existente.')
                return redirect('user_panel:bio_list')
            
            bio = form.save()
            messages.success(request, f'Bio criada com sucesso para o site {bio.site.domain}!')
            return redirect('user_panel:bio_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = SiteBioForm(user=request.user)
    
    context = {
        'title': 'Criar Bio',
        'breadcrumb': 'Bio > Criar',
        'form': form
    }
    return render(request, 'user_panel/bio/create.html', context)

@login_required
def bio_edit(request, bio_id):
    """Editar bio"""
    bio = get_object_or_404(SiteBio, id=bio_id)
    
    # Verificar permissão do usuário
    user_has_permission = AccountMembership.objects.filter(
        user=request.user,
        account=bio.site.account,
        status='active',
        role__in=['owner', 'admin']
    ).exists()
    
    if not user_has_permission:
        messages.error(request, 'Você não tem permissão para editar esta bio.')
        return redirect('user_panel:bio_list')
    
    if request.method == 'POST':
        form = SiteBioForm(request.POST, request.FILES, instance=bio, user=request.user)
        if form.is_valid():
            bio = form.save()
            messages.success(request, f'Bio atualizada com sucesso para o site {bio.site.domain}!')
            return redirect('user_panel:bio_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = SiteBioForm(instance=bio, user=request.user)
    
    context = {
        'title': 'Editar Bio',
        'breadcrumb': 'Bio > Editar',
        'form': form,
        'bio': bio
    }
    return render(request, 'user_panel/bio/edit.html', context)

@login_required
def bio_delete(request, bio_id):
    """Deletar bio"""
    bio = get_object_or_404(SiteBio, id=bio_id)
    
    # Verificar permissão do usuário
    user_has_permission = AccountMembership.objects.filter(
        user=request.user,
        account=bio.site.account,
        status='active',
        role__in=['owner', 'admin']
    ).exists()
    
    if not user_has_permission:
        messages.error(request, 'Você não tem permissão para deletar esta bio.')
        return redirect('user_panel:bio_list')
    
    if request.method == 'POST':
        site_domain = bio.site.domain
        bio.delete()
        messages.success(request, f'Bio do site {site_domain} foi deletada com sucesso!')
    
    return redirect('user_panel:bio_list')


@login_required
def categories_list(request):
    qs = SiteCategory.objects.filter(
        site__account__memberships__user=request.user,
        site__account__memberships__status='active'
    ).select_related('site').order_by('site__domain', 'name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(site__domain__icontains=search) |
            Q(site__account__name__icontains=search) |
            Q(site__bio__title__icontains=search)
        )
    context = {
        'title': 'Categorias',
        'breadcrumb': 'Categorias',
        'categories': qs,
        'search': search,
    }
    return render(request, 'user_panel/categories/list.html', context)

@login_required
def categories_create(request):
    if request.method == 'POST':
        form = SiteCategoryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'Categoria "{cat.name}" criada com sucesso.')
            return redirect('user_panel:categories_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
            # Exibir erros detalhados em toasts
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f'{label}: {error}')
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = SiteCategoryForm(user=request.user)
    return render(request, 'user_panel/categories/create.html', {'form': form, 'title': 'Criar Categoria'})

@login_required
def categories_edit(request, category_id):
    category = get_object_or_404(SiteCategory, id=category_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        form = SiteCategoryForm(request.POST, request.FILES, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso.')
            return redirect('user_panel:categories_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f'{label}: {error}')
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = SiteCategoryForm(instance=category, user=request.user)
    return render(request, 'user_panel/categories/edit.html', {'form': form, 'category': category, 'title': 'Editar Categoria'})

@login_required
def categories_delete(request, category_id):
    category = get_object_or_404(SiteCategory, id=category_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Categoria "{name}" removida.')
        return redirect('user_panel:categories_list')
    return render(request, 'user_panel/categories/delete.html', {'category': category, 'title': 'Remover Categoria'})


@login_required
def services_list(request):
    qs = Service.objects.filter(
        site__account__memberships__user=request.user,
        site__account__memberships__status='active'
    ).select_related('site', 'category').order_by('site__domain', 'order', 'title')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    context = {
        'title': 'Serviços',
        'breadcrumb': 'Serviços',
        'services': qs,
        'search': search,
    }
    return render(request, 'user_panel/services/list.html', context)

@login_required
def services_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Serviço "{service.title}" criado com sucesso.')
            return redirect('user_panel:services_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = ServiceForm(user=request.user)
    return render(request, 'user_panel/services/create.html', {'form': form, 'title': 'Criar Serviço'})

@login_required
def services_edit(request, service_id):
    service = get_object_or_404(Service, id=service_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso.')
            return redirect('user_panel:services_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = ServiceForm(instance=service, user=request.user)
    return render(request, 'user_panel/services/edit.html', {'form': form, 'service': service, 'title': 'Editar Serviço'})

@login_required
def services_delete(request, service_id):
    service = get_object_or_404(Service, id=service_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        title = service.title
        service.delete()
        messages.success(request, f'Serviço "{title}" removido.')
        return redirect('user_panel:services_list')
    return render(request, 'user_panel/services/delete.html', {'service': service, 'title': 'Remover Serviço'})


@login_required
def social_networks_list(request):
    qs = SocialNetwork.objects.filter(
        site__account__memberships__user=request.user,
        site__account__memberships__status='active'
    ).select_related('site').order_by('site__domain', 'network_type')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(url__icontains=search) | Q(network_type__icontains=search))
    context = {
        'title': 'Redes Sociais',
        'breadcrumb': 'Redes Sociais',
        'social_networks': qs,
        'search': search,
    }
    return render(request, 'user_panel/social_networks/list.html', context)

@login_required
def social_networks_create(request):
    if request.method == 'POST':
        form = SocialNetworkForm(request.POST, user=request.user)
        if form.is_valid():
            sn = form.save()
            messages.success(request, f'Rede social "{sn.get_network_type_display()}" adicionada.')
            return redirect('user_panel:social_networks_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = SocialNetworkForm(user=request.user)
    return render(request, 'user_panel/social_networks/create.html', {'form': form, 'title': 'Criar Rede Social'})

@login_required
def social_networks_edit(request, network_id):
    sn = get_object_or_404(SocialNetwork, id=network_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        form = SocialNetworkForm(request.POST, instance=sn, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rede social atualizada.')
            return redirect('user_panel:social_networks_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = SocialNetworkForm(instance=sn, user=request.user)
    return render(request, 'user_panel/social_networks/edit.html', {'form': form, 'social': sn, 'title': 'Editar Rede Social'})

@login_required
def social_networks_delete(request, network_id):
    sn = get_object_or_404(SocialNetwork, id=network_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        display = sn.get_network_type_display()
        sn.delete()
        messages.success(request, f'Rede social "{display}" removida.')
        return redirect('user_panel:social_networks_list')
    return render(request, 'user_panel/social_networks/delete.html', {'social': sn, 'title': 'Remover Rede Social'})


@login_required
def cta_list(request):
    qs = CTA.objects.filter(
        site__account__memberships__user=request.user,
        site__account__memberships__status='active'
    ).select_related('site').order_by('site__domain', 'order')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    return render(request, 'user_panel/cta/list.html', {
        'title': 'CTAs', 'breadcrumb': 'CTA', 'ctas': qs, 'search': search
    })

@login_required
def cta_create(request):
    if request.method == 'POST':
        form = CTAForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            cta = form.save()
            messages.success(request, f'CTA "{cta.title or cta.id}" criado.')
            return redirect('user_panel:cta_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = CTAForm(user=request.user)
    return render(request, 'user_panel/cta/create.html', {'form': form, 'title': 'Criar CTA'})

@login_required
def cta_edit(request, cta_id):
    cta = get_object_or_404(CTA, id=cta_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        form = CTAForm(request.POST, request.FILES, instance=cta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'CTA atualizado.')
            return redirect('user_panel:cta_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = CTAForm(instance=cta, user=request.user)
    return render(request, 'user_panel/cta/edit.html', {'form': form, 'cta': cta, 'title': 'Editar CTA'})

@login_required
def cta_delete(request, cta_id):
    cta = get_object_or_404(CTA, id=cta_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        title = cta.title or str(cta.id)
        cta.delete()
        messages.success(request, f'CTA "{title}" removido.')
        return redirect('user_panel:cta_list')
    return render(request, 'user_panel/cta/delete.html', {'cta': cta, 'title': 'Remover CTA'})


@login_required
def blog_list(request):
    qs = BlogPost.objects.filter(
        site__account__memberships__user=request.user,
        site__account__memberships__status='active'
    ).select_related('site', 'category').order_by('-published_at', '-created_at')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
    context = {
        'title': 'Blog',
        'breadcrumb': 'Blog',
        'posts': qs,
        'search': search,
    }
    return render(request, 'user_panel/blog/list.html', context)

@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'Post "{post.title or post.id}" criado.')
            return redirect('user_panel:blog_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = BlogPostForm(user=request.user)
    return render(request, 'user_panel/blog/create.html', {'form': form, 'title': 'Criar Post'})

@login_required
def blog_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post atualizado.')
            return redirect('user_panel:blog_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = BlogPostForm(instance=post, user=request.user)
    return render(request, 'user_panel/blog/edit.html', {'form': form, 'post': post, 'title': 'Editar Post'})

@login_required
def blog_delete(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id, site__account__memberships__user=request.user)
    if request.method == 'POST':
        title = post.title or str(post.id)
        post.delete()
        messages.success(request, f'Post "{title}" removido.')
        return redirect('user_panel:blog_list')
    return render(request, 'user_panel/blog/delete.html', {'post': post, 'title': 'Remover Post'})


# Banners Views
@login_required
def banners_list(request):
    """Lista de banners"""
    messages.info(request, 'Sistema de Banners em desenvolvimento')
    context = {
        'title': 'Banners',
        'breadcrumb': 'Banners'
    }
    return render(request, 'user_panel/banners/list.html', context)

@login_required
def banners_create(request):
    """Criar novo banner"""
    messages.info(request, 'Sistema de Banners em desenvolvimento')
    context = {
        'title': 'Criar Banner',
        'breadcrumb': 'Banners > Criar'
    }
    return render(request, 'user_panel/banners/create.html', context)

@login_required
def banners_edit(request, banner_id):
    """Editar banner"""
    messages.info(request, 'Sistema de Banners em desenvolvimento')
    context = {
        'title': 'Editar Banner',
        'breadcrumb': 'Banners > Editar'
    }
    return render(request, 'user_panel/banners/edit.html', context)

@login_required
def banners_delete(request, banner_id):
    """Deletar banner"""
    messages.info(request, 'Sistema de Banners em desenvolvimento')
    return redirect('user_panel:banners_list')

@login_required
def invite_user(request):
    """Convidar usuário"""
    messages.info(request, 'Funcionalidade de convite em desenvolvimento')
    return redirect('user_panel:dashboard')

@login_required
def api_keys(request):
    """Gerenciar chaves API"""
    messages.info(request, 'Sistema de API Keys em desenvolvimento')
    return redirect('user_panel:dashboard')

@login_required
def subscription_manage(request):
    """Gerenciar assinatura"""
    messages.info(request, 'Gerenciamento de assinatura em desenvolvimento')
    return redirect('user_panel:dashboard')


# ===== VIEWS DE ASSINATURAS =====

@user_panel_required
def subscriptions_list(request):
    """Lista todas as assinaturas"""
    from site_management.models import Subscription
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # Query base
    subscriptions = Subscription.objects.select_related('site', 'account', 'plan_type').all()
    
    # Aplicar filtros
    if search:
        subscriptions = subscriptions.filter(
            Q(site__domain__icontains=search) |
            Q(account__name__icontains=search) |
            Q(plan_type__title__icontains=search)
        )
    
    if status:
        subscriptions = subscriptions.filter(status=status)
    
    # Ordenação
    subscriptions = subscriptions.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'page_title': 'Assinaturas'
    }
    return render(request, 'user_panel/subscriptions/list.html', context)


@user_panel_required
def subscriptions_create(request):
    """Criar nova assinatura"""
    from site_management.models import Subscription, Site, PlanType
    from site_management.forms import SubscriptionForm
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Assinatura criada com sucesso!')
            return redirect('user_panel:subscriptions_list')
    else:
        form = SubscriptionForm()
    
    context = {
        'form': form,
        'page_title': 'Nova Assinatura'
    }
    return render(request, 'user_panel/subscriptions/form.html', context)


@user_panel_required
def subscriptions_edit(request, subscription_id):
    """Editar assinatura"""
    from site_management.models import Subscription
    from site_management.forms import SubscriptionForm
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assinatura atualizada com sucesso!')
            return redirect('user_panel:subscriptions_list')
    else:
        form = SubscriptionForm(instance=subscription)
    
    context = {
        'form': form,
        'subscription': subscription,
        'page_title': 'Editar Assinatura'
    }
    return render(request, 'user_panel/subscriptions/form.html', context)


@user_panel_required
def subscriptions_delete(request, subscription_id):
    """Deletar assinatura"""
    from site_management.models import Subscription
    
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Assinatura removida com sucesso!')
        return redirect('user_panel:subscriptions_list')
    
    context = {
        'subscription': subscription,
        'page_title': 'Remover Assinatura'
    }
    return render(request, 'user_panel/subscriptions/delete.html', context)


# ===== VIEWS DE PAGAMENTOS =====

@user_panel_required
def payments_list(request):
    """Lista todos os pagamentos"""
    from site_management.models import Payment
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    
    # Query base
    payments = Payment.objects.select_related('subscription', 'subscription__site', 'subscription__account').all()
    
    # Aplicar filtros
    if search:
        payments = payments.filter(
            Q(title__icontains=search) |
            Q(subscription__site__domain__icontains=search) |
            Q(subscription__account__name__icontains=search)
        )
    
    if status:
        payments = payments.filter(status=status)
        
    if month:
        payments = payments.filter(payment_month=month)
        
    if year:
        payments = payments.filter(payment_year=year)
    
    # Ordenação
    payments = payments.order_by('-payment_year', '-payment_month', '-created_at')
    
    # Paginação
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_payments = Payment.objects.count()
    paid_payments = Payment.objects.filter(status='paid').count()
    pending_payments = Payment.objects.filter(status='pending').count()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'month': month,
        'year': year,
        'total_payments': total_payments,
        'paid_payments': paid_payments,
        'pending_payments': pending_payments,
        'page_title': 'Pagamentos'
    }
    return render(request, 'user_panel/payments/list.html', context)


@user_panel_required
def payments_create(request):
    """Criar novo pagamento"""
    from site_management.models import Payment
    from site_management.forms import PaymentForm
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Pagamento criado com sucesso!')
            return redirect('user_panel:payments_list')
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'page_title': 'Novo Pagamento'
    }
    return render(request, 'user_panel/payments/form.html', context)


@user_panel_required
def payments_edit(request, payment_id):
    """Editar pagamento"""
    from site_management.models import Payment
    from site_management.forms import PaymentForm
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pagamento atualizado com sucesso!')
            return redirect('user_panel:payments_list')
    else:
        form = PaymentForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'page_title': 'Editar Pagamento'
    }
    return render(request, 'user_panel/payments/form.html', context)


@user_panel_required
def payments_delete(request, payment_id):
    """Deletar pagamento"""
    from site_management.models import Payment
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Pagamento removido com sucesso!')
        return redirect('user_panel:payments_list')
    
    context = {
        'payment': payment,
        'page_title': 'Remover Pagamento'
    }
    return render(request, 'user_panel/payments/delete.html', context)


# Views de Sites - Para o contexto do User Panel
@login_required
def sites_list(request):
    """Lista de sites do usuário"""
    from site_management.models import Site
    
    # Filtrar sites do usuário (através das contas que ele tem acesso)
    user_accounts = Account.objects.filter(
        memberships__user=request.user,
        memberships__status='active'
    )
    
    sites = Site.objects.filter(account__in=user_accounts).order_by('-created_at')
    
    # Paginação
    paginator = Paginator(sites, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sites': page_obj,
        'total_sites': sites.count(),
        'page_title': 'Meus Sites'
    }
    return render(request, 'user_panel/sites/list.html', context)

@login_required  
def site_create(request):
    """Criação de site no contexto do user panel"""
    from site_management.forms import SiteForm
    from site_management.models import TemplateCategory, PlanType
    
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            messages.success(request, f'Site "{site.domain}" criado com sucesso!')
            return redirect('user_panel:sites_list')
    else:
        form = SiteForm()
        # Filtrar apenas contas que o usuário tem acesso
        user_accounts = Account.objects.filter(
            memberships__user=request.user,
            memberships__status='active'
        )
        form.fields['account'].queryset = user_accounts
    
    context = {
        'form': form,
        'page_title': 'Criar Novo Site'
    }
    return render(request, 'user_panel/sites/create.html', context)

@login_required
def site_detail(request, site_id):
    """Detalhes do site no contexto do user panel"""
    from site_management.models import Site
    
    # Verificar se o usuário tem acesso ao site
    user_accounts = Account.objects.filter(
        memberships__user=request.user,
        memberships__status='active'
    )
    
    site = get_object_or_404(Site, id=site_id, account__in=user_accounts)
    
    context = {
        'site': site,
        'page_title': f'Site: {site.domain}'
    }
    return render(request, 'user_panel/sites/detail.html', context)


@user_panel_required
def site_edit(request, site_id):
    """Editar site no contexto do user panel"""
    from site_management.forms import SiteForm
    from site_management.models import Site
    
    # Verificar se o usuário tem acesso ao site
    user_accounts = Account.objects.filter(
        memberships__user=request.user,
        memberships__status='active'
    )
    
    site = get_object_or_404(Site, id=site_id, account__in=user_accounts)
    
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            messages.success(request, f'Site "{site.domain}" atualizado com sucesso!')
            return redirect('user_panel:site_detail', site_id=site.id)
    else:
        form = SiteForm(instance=site)
        # Filtrar apenas contas que o usuário tem acesso
        user_accounts = Account.objects.filter(
            memberships__user=request.user,
            memberships__status='active'
        )
        form.fields['account'].queryset = user_accounts
    
    context = {
        'form': form,
        'site': site,
        'page_title': f'Editar Site: {site.domain}'
    }
    return render(request, 'user_panel/sites/edit.html', context)
