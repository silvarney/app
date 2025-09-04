from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import Account, AccountMembership
from .models import (
    Site, SiteBio, SocialNetwork, Banner, CTA, 
    SiteCategory, Service, BlogPost, TemplateCategory,
    PlanType, Item, Subscription, Payment, SubscriptionItem
)
from .forms import SiteForm


def check_site_permission(user, site, required_role='member'):
    """Verifica se o usuário tem permissão no site através da conta"""
    if user.is_superuser:
        return True
    
    try:
        membership = AccountMembership.objects.get(
            account=site.account, 
            user=user, 
            status='active'
        )
        if required_role == 'owner':
            return membership.role == 'owner'
        elif required_role == 'admin':
            return membership.role in ['owner', 'admin']
        else:
            return True
    except AccountMembership.DoesNotExist:
        return False


@login_required
def sites_list(request):
    """Lista de sites do usuário"""
    user = request.user
    
    # Buscar contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    # Buscar sites das contas do usuário
    sites = Site.objects.filter(
        account__in=user_accounts
    ).select_related('account', 'plan_type').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    account_filter = request.GET.get('account', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        sites = sites.filter(
            Q(name__icontains=search) |
            Q(domain__icontains=search) |
            Q(account__name__icontains=search)
        )
    
    if account_filter:
        sites = sites.filter(account_id=account_filter)
    
    if status_filter:
        sites = sites.filter(status='active' if status_filter == 'active' else 'inactive')
    
    # Paginação
    paginator = Paginator(sites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sites': page_obj,
        'user_accounts': user_accounts,
        'search': search,
        'account_filter': account_filter,
        'status_filter': status_filter,
        'total_sites': sites.count(),
    }
    
    return render(request, 'site_management/sites/list.html', context)


@login_required
def site_detail(request, site_id):
    """Detalhes de um site específico"""
    site = get_object_or_404(Site, id=site_id)
    
    if not check_site_permission(request.user, site):
        raise PermissionDenied("Você não tem permissão para acessar este site.")
    
    # Dados relacionados
    site_bio = getattr(site, 'bio', None)
    social_networks = site.social_networks.all()
    banners = site.banners.all()
    ctas = site.ctas.all()
    categories = site.categories.all()
    services = site.services.all()[:6]  # Últimos 6 serviços
    blog_posts = site.blog_posts.filter(is_active=True)[:6]  # Últimos 6 posts
    
    # Estatísticas
    stats = {
        'total_services': site.services.count(),
        'active_services': site.services.filter(is_active=True).count(),
        'total_blog_posts': site.blog_posts.count(),
        'active_blog_posts': site.blog_posts.filter(is_active=True).count(),
        'total_categories': categories.count(),
        'total_banners': banners.count(),
    }
    
    context = {
        'site': site,
        'site_bio': site_bio,
        'social_networks': social_networks,
        'banners': banners,
        'ctas': ctas,
        'categories': categories,
        'services': services,
        'blog_posts': blog_posts,
        'stats': stats,
        'can_manage': check_site_permission(request.user, site, 'admin'),
    }
    
    return render(request, 'site_management/sites/detail.html', context)


@login_required
def site_create(request):
    """Criar novo site"""
    user = request.user
    
    # Detectar se está sendo acessado pelo admin_panel
    is_admin_panel = '/admin-panel/' in request.path
    
    # Para admin_panel, permitir acesso a todas as contas se for staff
    if is_admin_panel and user.is_staff:
        user_accounts = Account.objects.filter(status='active')
    else:
        # Buscar contas onde o usuário pode criar sites
        user_accounts = Account.objects.filter(
            memberships__user=user,
            memberships__role__in=['owner', 'admin'],
            memberships__status='active'
        ).distinct()
    
    if not user_accounts.exists():
        messages.error(request, 'Você não tem permissão para criar sites.')
        return redirect('site_management:sites_list')
    
    if request.method == 'POST':
        form = SiteForm(request.POST, user=user, is_admin_panel=is_admin_panel)
        if form.is_valid():
            try:
                with transaction.atomic():
                    site = form.save()
                    
                    # Criar bio padrão
                    SiteBio.objects.create(
                        site=site,
                        title=site.domain,
                        description=f'Site {site.domain}'
                    )
                    
                    messages.success(request, f'Site "{site.domain}" criado com sucesso!')
                    return redirect('site_management:site_detail', site_id=site.id)
                    
            except Exception as e:
                messages.error(request, f'Erro ao criar site: {str(e)}')
        else:
            # Exibir erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = SiteForm(user=user, is_admin_panel=is_admin_panel)
    
    context = {
        'form': form,
    }
    
    # Escolher template baseado no painel
    if is_admin_panel:
        template_name = 'admin_panel/sites/create.html'
    else:
        template_name = 'site_management/sites/create.html'
    
    return render(request, template_name, context)


@login_required
def site_edit(request, site_id):
    """Editar site existente"""
    site = get_object_or_404(Site, id=site_id)
    
    if not check_site_permission(request.user, site, 'admin'):
        raise PermissionDenied("Você não tem permissão para editar este site.")
    
    if request.method == 'POST':
        # Campo name removido - não existe no modelo Site
        domain = request.POST.get('domain', '').strip()
        plan_type_id = request.POST.get('plan_type')
        description = request.POST.get('description', '').strip()
        
        # Validações
        if not all([domain, plan_type_id]):
            messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
        else:
            try:
                plan_type = PlanType.objects.get(id=plan_type_id)
                
                # Verificar se o domínio já existe (exceto o atual)
                if Site.objects.filter(domain=domain).exclude(id=site.id).exists():
                    messages.error(request, 'Este domínio já está sendo usado por outro site.')
                else:
                    # Campo name não existe no modelo Site
                    site.domain = domain
                    site.plan_type = plan_type
                    site.description = description
                    site.save()
                    
                    messages.success(request, f'Site "{domain}" atualizado com sucesso!')
                    return redirect('site_management:site_detail', site_id=site.id)
                    
            except PlanType.DoesNotExist:
                messages.error(request, 'Tipo de plano inválido.')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar site: {str(e)}')
    
    # Buscar tipos de plano disponíveis
    plan_types = PlanType.objects.filter(is_active=True)
    
    context = {
        'site': site,
        'plan_types': plan_types,
        'is_edit': True,
    }
    
    return render(request, 'site_management/sites/form.html', context)


@login_required
@require_http_methods(["POST"])
def site_toggle_status(request, site_id):
    """Ativar/desativar site"""
    site = get_object_or_404(Site, id=site_id)
    
    if not check_site_permission(request.user, site, 'admin'):
        raise PermissionDenied("Você não tem permissão para alterar este site.")
    
    site.status = 'inactive' if site.status == 'active' else 'active'
    site.save()
    
    status_text = 'ativado' if site.status == 'active' else 'desativado'
    messages.success(request, f'Site "{site.domain}" {status_text} com sucesso!')
    
    return redirect('site_management:site_detail', site_id=site.id)


@login_required
@require_http_methods(["POST"])
def site_delete(request, site_id):
    """Excluir site com confirmação por senha"""
    site = get_object_or_404(Site, id=site_id)
    
    if not check_site_permission(request.user, site, 'owner'):
        raise PermissionDenied("Apenas proprietários podem excluir sites.")
    
    password = request.POST.get('password', '')
    
    if not password:
        messages.error(request, 'Senha é obrigatória para excluir o site.')
        return redirect('site_management:site_detail', site_id=site.id)
    
    # Verificar senha do usuário
    user = authenticate(username=request.user.email, password=password)
    if user != request.user:
        messages.error(request, 'Senha incorreta.')
        return redirect('site_management:site_detail', site_id=site.id)
    
    site_name = site.domain
    
    try:
        with transaction.atomic():
            site.delete()
        
        messages.success(request, f'Site "{site_name}" excluído com sucesso!')
        return redirect('site_management:sites_list')
        
    except Exception as e:
        messages.error(request, f'Erro ao excluir site: {str(e)}')
        return redirect('site_management:site_detail', site_id=site.id)


# Views para Bio do Site
@login_required
def site_bio_edit(request, site_id):
    """Editar bio do site"""
    site = get_object_or_404(Site, id=site_id)
    
    if not check_site_permission(request.user, site, 'admin'):
        raise PermissionDenied("Você não tem permissão para editar este site.")
    
    bio, created = SiteBio.objects.get_or_create(site=site)
    
    if request.method == 'POST':
        bio.title = request.POST.get('title', '').strip()
        bio.description = request.POST.get('description', '').strip()
        bio.email = request.POST.get('email', '').strip()
        bio.whatsapp = request.POST.get('whatsapp', '').strip()
        bio.phone = request.POST.get('phone', '').strip()
        bio.address = request.POST.get('address', '').strip()
        bio.google_maps_url = request.POST.get('google_maps_url', '').strip()
        
        # Upload de arquivos
        if 'favicon' in request.FILES:
            bio.favicon = request.FILES['favicon']
        if 'logo' in request.FILES:
            bio.logo = request.FILES['logo']
        
        bio.save()
        
        messages.success(request, 'Informações do site atualizadas com sucesso!')
        return redirect('site_management:site_detail', site_id=site.id)
    
    context = {
        'site': site,
        'bio': bio,
    }
    
    return render(request, 'site_management/sites/bio_form.html', context)


# Views para Dashboard/Analytics
@login_required
def sites_dashboard(request):
    """Dashboard de sites do usuário"""
    user = request.user
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Buscar contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    ).distinct()
    
    # Sites do usuário
    user_sites = Site.objects.filter(account__in=user_accounts)
    
    # Estatísticas gerais
    stats = {
        'total_sites': user_sites.count(),
        'active_sites': user_sites.filter(status='active').count(),
        'inactive_sites': user_sites.filter(status='inactive').count(),
        'recent_sites': user_sites.filter(created_at__gte=start_date).count(),
    }
    
    # Sites por plano
    plan_distribution = user_sites.values(
        'plan_type__title'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Sites mais recentes
    recent_sites = user_sites.order_by('-created_at')[:5]
    
    # Sites por conta
    sites_by_account = user_sites.values(
        'account__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'stats': stats,
        'plan_distribution': plan_distribution,
        'recent_sites': recent_sites,
        'sites_by_account': sites_by_account,
        'days': days,
    }
    
    return render(request, 'site_management/dashboard.html', context)
