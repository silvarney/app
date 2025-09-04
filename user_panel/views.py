from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
import json
import csv

from accounts.models import Account, AccountMembership
from users.models import User
from permissions.models import Permission, Role, UserRole
from content.models import Content, Category, Tag
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


# ==================== GERENCIAMENTO DE CONTEÚDO ====================

@login_required
def content_list(request):
    """Lista todo o conteúdo do usuário"""
    user = request.user
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    account_filter = request.GET.get('account', '')
    
    # Contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    )
    
    # Query base - conteúdo das contas do usuário
    contents = Content.objects.filter(
        account__in=user_accounts
    ).select_related('account', 'category', 'author').prefetch_related('tags')
    
    # Filtros
    if search:
        contents = contents.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(meta_description__icontains=search)
        )
    
    if status_filter:
        contents = contents.filter(status=status_filter)
    
    if category_filter:
        contents = contents.filter(category_id=category_filter)
    
    if account_filter:
        contents = contents.filter(account_id=account_filter)
    
    contents = contents.order_by('-updated_at')
    
    # Paginação
    paginator = Paginator(contents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Choices para filtros
    categories = Category.objects.filter(
        account__in=user_accounts
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status_filter,
        'category': category_filter,
        'account': account_filter,
        'categories': categories,
        'user_accounts': user_accounts,
        'status_choices': Content.STATUS_CHOICES,
    }
    
    return render(request, 'user_panel/content/list.html', context)


@login_required
def content_create(request):
    """Criar novo conteúdo"""
    user = request.user
    
    # Contas onde o usuário pode criar conteúdo
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__role__in=['owner', 'admin', 'editor'],
        memberships__status='active'
    )
    
    if not user_accounts.exists():
        messages.error(request, 'Você não tem permissão para criar conteúdo.')
        return redirect('user_panel:content_list')
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        account = get_object_or_404(user_accounts, id=account_id)
        
        # Criar conteúdo
        content = Content.objects.create(
            account=account,
            author=user,
            title=request.POST.get('title'),
            slug=request.POST.get('slug'),
            content=request.POST.get('content', ''),
            excerpt=request.POST.get('excerpt', ''),
            meta_title=request.POST.get('meta_title', ''),
            meta_description=request.POST.get('meta_description', ''),
            status=request.POST.get('status', 'draft'),
            content_type=request.POST.get('content_type', 'page')
        )
        
        # Categoria
        category_id = request.POST.get('category')
        if category_id:
            try:
                category = Category.objects.get(
                    id=category_id,
                    account=account
                )
                content.category = category
                content.save()
            except Category.DoesNotExist:
                pass
        
        # Tags
        tags_input = request.POST.get('tags', '')
        if tags_input:
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    account=account
                )
                content.tags.add(tag)
        
        messages.success(request, 'Conteúdo criado com sucesso!')
        return redirect('user_panel:content_detail', content_id=content.id)
    
    # Categorias disponíveis
    categories = Category.objects.filter(
        account__in=user_accounts
    ).order_by('name')
    
    context = {
        'user_accounts': user_accounts,
        'categories': categories,
        'content_types': Content.CONTENT_TYPE_CHOICES,
        'status_choices': Content.STATUS_CHOICES,
    }
    
    return render(request, 'user_panel/content/create.html', context)


@login_required
def content_detail(request, content_id):
    """Detalhes do conteúdo"""
    user = request.user
    
    # Verificar acesso
    content = get_object_or_404(
        Content,
        id=content_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    # Verificar permissão de visualização
    user_membership = AccountMembership.objects.get(
        account=content.account,
        user=user,
        status='active'
    )
    
    can_edit = user_membership.role in ['owner', 'admin', 'editor'] or content.author == user
    
    context = {
        'content': content,
        'can_edit': can_edit,
    }
    
    return render(request, 'user_panel/content/detail.html', context)


@login_required
def content_edit(request, content_id):
    """Editar conteúdo"""
    user = request.user
    
    # Verificar acesso e permissão
    content = get_object_or_404(
        Content,
        id=content_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    user_membership = AccountMembership.objects.get(
        account=content.account,
        user=user,
        status='active'
    )
    
    can_edit = user_membership.role in ['owner', 'admin', 'editor'] or content.author == user
    
    if not can_edit:
        messages.error(request, 'Você não tem permissão para editar este conteúdo.')
        return redirect('user_panel:content_detail', content_id=content.id)
    
    if request.method == 'POST':
        # Atualizar conteúdo
        content.title = request.POST.get('title', content.title)
        content.slug = request.POST.get('slug', content.slug)
        content.content = request.POST.get('content', content.content)
        content.excerpt = request.POST.get('excerpt', content.excerpt)
        content.meta_title = request.POST.get('meta_title', content.meta_title)
        content.meta_description = request.POST.get('meta_description', content.meta_description)
        content.status = request.POST.get('status', content.status)
        content.content_type = request.POST.get('content_type', content.content_type)
        
        # Categoria
        category_id = request.POST.get('category')
        if category_id:
            try:
                category = Category.objects.get(
                    id=category_id,
                    account=content.account
                )
                content.category = category
            except Category.DoesNotExist:
                content.category = None
        else:
            content.category = None
        
        content.save()
        
        # Tags
        content.tags.clear()
        tags_input = request.POST.get('tags', '')
        if tags_input:
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    account=content.account
                )
                content.tags.add(tag)
        
        messages.success(request, 'Conteúdo atualizado com sucesso!')
        return redirect('user_panel:content_detail', content_id=content.id)
    
    # Categorias disponíveis
    categories = Category.objects.filter(
        account=content.account
    ).order_by('name')
    
    # Tags atuais
    current_tags = ', '.join([tag.name for tag in content.tags.all()])
    
    context = {
        'content': content,
        'categories': categories,
        'current_tags': current_tags,
        'content_types': Content.CONTENT_TYPE_CHOICES,
        'status_choices': Content.STATUS_CHOICES,
    }
    
    return render(request, 'user_panel/content/edit.html', context)


@login_required
@require_http_methods(["POST"])
def content_delete(request, content_id):
    """Deletar conteúdo"""
    user = request.user
    
    # Verificar acesso e permissão
    content = get_object_or_404(
        Content,
        id=content_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    user_membership = AccountMembership.objects.get(
        account=content.account,
        user=user,
        status='active'
    )
    
    can_delete = user_membership.role in ['owner', 'admin'] or content.author == user
    
    if not can_delete:
        messages.error(request, 'Você não tem permissão para deletar este conteúdo.')
        return redirect('user_panel:content_detail', content_id=content.id)
    
    content_title = content.title
    content.delete()
    
    messages.success(request, f'Conteúdo "{content_title}" deletado com sucesso!')
    return redirect('user_panel:content_list')


@login_required
@require_http_methods(["POST"])
def content_toggle_status(request, content_id):
    """Alternar status do conteúdo (publicado/rascunho)"""
    user = request.user
    
    # Verificar acesso e permissão
    content = get_object_or_404(
        Content,
        id=content_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    user_membership = AccountMembership.objects.get(
        account=content.account,
        user=user,
        status='active'
    )
    
    can_publish = user_membership.role in ['owner', 'admin', 'editor'] or content.author == user
    
    if not can_publish:
        return JsonResponse({'success': False, 'error': 'Sem permissão'})
    
    # Alternar status
    if content.status == 'published':
        content.status = 'draft'
        action = 'despublicado'
    else:
        content.status = 'published'
        content.published_at = timezone.now()
        action = 'publicado'
    
    content.save()
    
    return JsonResponse({
        'success': True,
        'status': content.status,
        'message': f'Conteúdo {action} com sucesso!'
    })


@login_required
def settings(request):
    """Página de configurações do usuário"""
    user = request.user
    
    # Verificar se o usuário tem permissão para gerenciar configurações da conta
    can_manage_account = False
    if hasattr(user, 'account_membership') and user.account_membership:
        can_manage_account = user.account_membership.can_manage_settings
    
    context = {
        'user': user,
        'can_manage_account': can_manage_account,
        'is_admin': user.is_staff,
    }
    
    return render(request, 'user_panel/settings.html', context)
