from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from permissions.decorators import user_has_permission, user_has_role
from permissions.models import Permission
from accounts.models import Account


class IsAuthenticatedAndAccountMember(permissions.BasePermission):
    """
    Permissão que verifica se o usuário está autenticado e é membro da conta.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Obter conta do contexto
        account = self.get_account_from_request(request, view)
        if not account:
            return False
        
        # Verificar se é membro da conta
        return request.user.account_memberships.filter(
            account=account, 
            is_active=True
        ).exists()
    
    def get_account_from_request(self, request, view):
        """
        Obtém a conta do contexto da requisição.
        """
        # Tentar obter do queryset (para ViewSets)
        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            if hasattr(queryset.model, 'account'):
                # Se o modelo tem campo account, usar a primeira conta do usuário
                membership = request.user.memberships.first()
                if membership:
                    return membership.account
        
        # Tentar obter dos parâmetros da URL
        account_id = (
            view.kwargs.get('account_id') or
            request.GET.get('account_id') or
            request.data.get('account_id') if hasattr(request, 'data') else None
        )
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Tentar obter da sessão
        account_id = request.session.get('current_account_id')
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Usar primeira conta do usuário como fallback
        membership = request.user.memberships.first()
        if membership:
            return membership.account
        
        return None


class HasPermission(permissions.BasePermission):
    """
    Permissão que verifica se o usuário tem uma permissão específica.
    """
    
    def __init__(self, permission_codename):
        self.permission_codename = permission_codename
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Obter conta do contexto
        account = self.get_account_from_request(request, view)
        
        # Verificar permissão
        try:
            permission = Permission.objects.get(
                codename=self.permission_codename, 
                is_active=True
            )
            return user_has_permission(request.user, permission, account)
        except Permission.DoesNotExist:
            return False
    
    def get_account_from_request(self, request, view):
        """
        Obtém a conta do contexto da requisição.
        """
        # Tentar obter do queryset (para ViewSets)
        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            if hasattr(queryset.model, 'account'):
                # Se o modelo tem campo account, usar a primeira conta do usuário
                membership = request.user.memberships.first()
                if membership:
                    return membership.account
        
        # Tentar obter dos parâmetros da URL
        account_id = (
            view.kwargs.get('account_id') or
            request.GET.get('account_id') or
            request.data.get('account_id') if hasattr(request, 'data') else None
        )
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Tentar obter da sessão
        account_id = request.session.get('current_account_id')
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Usar primeira conta do usuário como fallback
        membership = request.user.memberships.first()
        if membership:
            return membership.account
        
        return None


class HasRole(permissions.BasePermission):
    """
    Permissão que verifica se o usuário tem uma função específica.
    """
    
    def __init__(self, role_codename):
        self.role_codename = role_codename
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Obter conta do contexto
        account = self.get_account_from_request(request, view)
        
        # Verificar função
        return user_has_role(request.user, self.role_codename, account)
    
    def get_account_from_request(self, request, view):
        """
        Obtém a conta do contexto da requisição.
        """
        # Tentar obter do queryset (para ViewSets)
        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            if hasattr(queryset.model, 'account'):
                # Se o modelo tem campo account, usar a primeira conta do usuário
                membership = request.user.memberships.first()
                if membership:
                    return membership.account
        
        # Tentar obter dos parâmetros da URL
        account_id = (
            view.kwargs.get('account_id') or
            request.GET.get('account_id') or
            request.data.get('account_id') if hasattr(request, 'data') else None
        )
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Tentar obter da sessão
        account_id = request.session.get('current_account_id')
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        # Usar primeira conta do usuário como fallback
        membership = request.user.memberships.first()
        if membership:
            return membership.account
        
        return None


class ContentPermission(permissions.BasePermission):
    """
    Permissão específica para gerenciamento de conteúdo.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Mapear ações para permissões
        action_permissions = {
            'list': 'read_content',
            'retrieve': 'read_content',
            'create': 'create_content',
            'update': 'update_content',
            'partial_update': 'update_content',
            'destroy': 'delete_content',
            'publish': 'manage_content',
            'unpublish': 'manage_content',
            'duplicate': 'create_content',
        }
        
        action = getattr(view, 'action', None)
        if action not in action_permissions:
            return False
        
        permission_codename = action_permissions[action]
        
        # Obter conta do contexto
        account = self.get_account_from_request(request, view)
        
        # Verificar permissão
        try:
            permission = Permission.objects.get(
                codename=permission_codename, 
                is_active=True
            )
            return user_has_permission(request.user, permission, account)
        except Permission.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permissão no nível do objeto.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Verificar se o usuário tem acesso à conta do objeto
        if hasattr(obj, 'account'):
            if not request.user.memberships.filter(
                 account=obj.account, 
                 status='active'
             ).exists():
                return False
        
        # Para operações de escrita, verificar se é o autor ou tem permissão de gerenciar
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if hasattr(obj, 'author') and obj.author == request.user:
                return True
            
            # Verificar permissão de gerenciar
            try:
                permission = Permission.objects.get(
                    codename='manage_content', 
                    is_active=True
                )
                return user_has_permission(
                    request.user, 
                    permission, 
                    getattr(obj, 'account', None)
                )
            except Permission.DoesNotExist:
                return False
        
        return True
    
    def get_account_from_request(self, request, view):
        """
        Obtém a conta do contexto da requisição.
        """
        # Usar primeira conta do usuário como fallback
        membership = request.user.memberships.first()
        if membership:
            return membership.account
        
        return None


class DomainPermission(permissions.BasePermission):
    """
    Permissão específica para gerenciamento de domínios.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Mapear ações para permissões
        action_permissions = {
            'list': 'read_domain',
            'retrieve': 'read_domain',
            'create': 'create_domain',
            'update': 'update_domain',
            'partial_update': 'update_domain',
            'destroy': 'delete_domain',
            'verify': 'manage_domain',
            'set_primary': 'manage_domain',
        }
        
        action = getattr(view, 'action', None)
        if action not in action_permissions:
            return False
        
        permission_codename = action_permissions[action]
        
        # Obter conta do contexto
        account = self.get_account_from_request(request, view)
        
        # Verificar permissão
        try:
            permission = Permission.objects.get(
                codename=permission_codename, 
                is_active=True
            )
            return user_has_permission(request.user, permission, account)
        except Permission.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica permissão no nível do objeto.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre tem acesso
        if request.user.is_superuser:
            return True
        
        # Verificar se o usuário tem acesso à conta do objeto
        if hasattr(obj, 'account'):
            if not request.user.memberships.filter(
                 account=obj.account, 
                 status='active'
             ).exists():
                return False
        
        return True
    
    def get_account_from_request(self, request, view):
        """
        Obtém a conta do contexto da requisição.
        """
        # Usar primeira conta do usuário como fallback
        membership = request.user.memberships.first()
        if membership:
            return membership.account
        
        return None