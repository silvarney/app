from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Permission, UserPermission, UserRole
from accounts.models import Account


def admin_required(view_func):
    """
    Decorator para garantir que apenas usuários staff acessem views do admin panel.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            # Se não for staff, redireciona para o painel do usuário
            if request.path.startswith('/admin-panel/'):
                return redirect('user_panel:dashboard')
            raise PermissionDenied('Você não tem permissão para acessar o painel administrativo.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_panel_required(view_func):
    """
    Decorator para garantir que usuários staff não acessem views do user panel 
    (exceto se especificamente permitido).
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Staff pode acessar user panel se necessário, mas por padrão redireciona para admin
        if request.user.is_staff and not request.GET.get('force_user_panel'):
            if request.path.startswith('/user-panel/'):
                return redirect('admin_panel:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required(permission_codename, account_required=True):
    """
    Decorator para verificar se o usuário tem uma permissão específica.
    
    Args:
        permission_codename (str): Código da permissão necessária
        account_required (bool): Se True, verifica permissão no contexto da conta
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Superusuário sempre tem acesso
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar se a permissão existe
            try:
                permission = Permission.objects.get(codename=permission_codename, is_active=True)
            except Permission.DoesNotExist:
                raise PermissionDenied(f"Permissão '{permission_codename}' não encontrada")
            
            # Se account_required, verificar no contexto da conta
            if account_required:
                account_id = kwargs.get('account_id') or request.GET.get('account_id')
                if not account_id:
                    # Tentar obter da sessão ou primeira conta do usuário
                    account_id = request.session.get('current_account_id')
                    if not account_id:
                        membership = user.account_memberships.first()
                        if membership:
                            account_id = membership.account.id
                
                if not account_id:
                    raise PermissionDenied("Conta não especificada")
                
                account = get_object_or_404(Account, id=account_id)
                
                # Verificar se o usuário tem acesso à conta
                if not user.account_memberships.filter(account=account).exists():
                    raise PermissionDenied("Usuário não tem acesso a esta conta")
                
                # Verificar permissão no contexto da conta
                has_permission = user_has_permission(user, permission, account)
            else:
                # Verificar permissão global
                has_permission = user_has_permission(user, permission)
            
            if not has_permission:
                if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse(
                        {'error': f"Permissão '{permission.name}' necessária"},
                        status=403
                    )
                raise PermissionDenied(f"Permissão '{permission.name}' necessária")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(role_codename, account_required=True):
    """
    Decorator para verificar se o usuário tem uma função específica.
    
    Args:
        role_codename (str): Código da função necessária
        account_required (bool): Se True, verifica função no contexto da conta
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Superusuário sempre tem acesso
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Se account_required, verificar no contexto da conta
            if account_required:
                account_id = kwargs.get('account_id') or request.GET.get('account_id')
                if not account_id:
                    # Tentar obter da sessão ou primeira conta do usuário
                    account_id = request.session.get('current_account_id')
                    if not account_id:
                        membership = user.account_memberships.first()
                        if membership:
                            account_id = membership.account.id
                
                if not account_id:
                    raise PermissionDenied("Conta não especificada")
                
                account = get_object_or_404(Account, id=account_id)
                
                # Verificar se o usuário tem acesso à conta
                if not user.account_memberships.filter(account=account).exists():
                    raise PermissionDenied("Usuário não tem acesso a esta conta")
                
                # Verificar função no contexto da conta
                has_role = user_has_role(user, role_codename, account)
            else:
                # Verificar função global
                has_role = user_has_role(user, role_codename)
            
            if not has_role:
                if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse(
                        {'error': f"Função '{role_codename}' necessária"},
                        status=403
                    )
                raise PermissionDenied(f"Função '{role_codename}' necessária")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def account_member_required(view_func):
    """
    Decorator para verificar se o usuário é membro da conta especificada.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        # Superusuário sempre tem acesso
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        account_id = kwargs.get('account_id') or request.GET.get('account_id')
        if not account_id:
            # Tentar obter da sessão
            account_id = request.session.get('account_id')
        if not account_id:
            raise PermissionDenied("Conta não especificada")
        
        account = get_object_or_404(Account, id=account_id)
        
        # Verificar se o usuário é membro da conta
        if not user.account_memberships.filter(account=account).exists():
            if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                return JsonResponse(
                    {'error': 'Usuário não é membro desta conta'},
                    status=403
                )
            raise PermissionDenied("Usuário não é membro desta conta")
        
        # Adicionar a conta ao request para uso posterior
        request.current_account = account
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_has_permission(user, permission, account=None):
    """
    Verifica se um usuário tem uma permissão específica.
    
    Args:
        user: Instância do usuário
        permission: Instância da permissão ou código da permissão
        account: Instância da conta (opcional)
    
    Returns:
        bool: True se o usuário tem a permissão
    """
    if user.is_superuser:
        return True
    
    if isinstance(permission, str):
        try:
            permission = Permission.objects.get(codename=permission, is_active=True)
        except Permission.DoesNotExist:
            return False
    
    # Verificar permissão direta do usuário
    user_permission_query = UserPermission.objects.filter(
        user=user,
        permission=permission,
        is_active=True
    )
    
    if account:
        user_permission_query = user_permission_query.filter(account=account)
    
    if user_permission_query.exists():
        return True
    
    # Verificar permissão através de funções
    user_roles_query = UserRole.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        role__permissions=permission
    )
    
    if account:
        user_roles_query = user_roles_query.filter(account=account)
    
    return user_roles_query.exists()


def user_has_role(user, role_codename, account=None):
    """
    Verifica se um usuário tem uma função específica.
    
    Args:
        user: Instância do usuário
        role_codename: Código da função
        account: Instância da conta (opcional)
    
    Returns:
        bool: True se o usuário tem a função
    """
    if user.is_superuser:
        return True
    
    user_roles_query = UserRole.objects.filter(
        user=user,
        role__codename=role_codename,
        role__is_active=True,
        is_active=True
    )
    
    if account:
        user_roles_query = user_roles_query.filter(account=account)
    
    return user_roles_query.exists()


def get_user_permissions(user, account=None):
    """
    Obtém todas as permissões de um usuário.
    
    Args:
        user: Instância do usuário
        account: Instância da conta (opcional)
    
    Returns:
        QuerySet: Permissões do usuário
    """
    if user.is_superuser:
        return Permission.objects.filter(is_active=True)
    
    # Permissões diretas
    direct_permissions_query = Permission.objects.filter(
        user_permissions__user=user,
        user_permissions__is_active=True,
        is_active=True
    )
    
    # Permissões através de funções
    role_permissions_query = Permission.objects.filter(
        roles__user_roles__user=user,
        roles__user_roles__is_active=True,
        roles__is_active=True,
        is_active=True
    )
    
    if account:
        direct_permissions_query = direct_permissions_query.filter(
            user_permissions__account=account
        )
        role_permissions_query = role_permissions_query.filter(
            roles__user_roles__account=account
        )
    
    # Combinar as duas consultas
    return (direct_permissions_query | role_permissions_query).distinct()


def get_user_roles(user, account=None):
    """
    Obtém todas as funções de um usuário.
    
    Args:
        user: Instância do usuário
        account: Instância da conta (opcional)
    
    Returns:
        QuerySet: Funções do usuário
    """
    from .models import Role
    
    if user.is_superuser:
        return Role.objects.filter(is_active=True)
    
    user_roles_query = Role.objects.filter(
        user_roles__user=user,
        user_roles__is_active=True,
        is_active=True
    )
    
    if account:
        user_roles_query = user_roles_query.filter(
            user_roles__account=account
        )
    
    return user_roles_query.distinct()