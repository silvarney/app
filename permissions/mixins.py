from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .decorators import user_has_permission, user_has_role, get_user_permissions
from .models import Permission
from accounts.models import Account


class PermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin para verificar permissões em views baseadas em classe.
    """
    permission_required = None
    account_required = True
    raise_exception = True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self):
        """
        Verifica se o usuário tem a permissão necessária.
        """
        if not self.permission_required:
            return True
        
        user = self.request.user
        
        # Superusuário sempre tem acesso
        if user.is_superuser:
            return True
        
        # Verificar se a permissão existe
        try:
            permission = Permission.objects.get(
                codename=self.permission_required, 
                is_active=True
            )
        except Permission.DoesNotExist:
            return False
        
        # Se account_required, verificar no contexto da conta
        if self.account_required:
            account = self.get_account()
            if not account:
                return False
            
            # Verificar se o usuário tem acesso à conta
            if not user.account_memberships.filter(account=account, status='active').exists():
                return False
            
            return user_has_permission(user, permission, account)
        else:
            return user_has_permission(user, permission)
    
    def get_account(self):
        """
        Obtém a conta do contexto da requisição.
        """
        account_id = (
            self.kwargs.get('account_id') or 
            self.request.GET.get('account_id') or
            self.request.session.get('current_account_id')
        )
        
        if not account_id:
            # Tentar obter da primeira conta do usuário
            membership = self.request.user.account_memberships.first()
            if membership:
                account_id = membership.account.id
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        return None
    
    def handle_no_permission(self):
        """
        Lida com a falta de permissão.
        """
        if self.request.headers.get('Content-Type') == 'application/json' or self.request.path.startswith('/api/'):
            return JsonResponse(
                {'error': f"Permissão '{self.permission_required}' necessária"},
                status=403
            )
        
        if self.raise_exception:
            raise PermissionDenied(f"Permissão '{self.permission_required}' necessária")
        
        return super().handle_no_permission()


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin para verificar funções em views baseadas em classe.
    """
    role_required = None
    account_required = True
    raise_exception = True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_role():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def has_role(self):
        """
        Verifica se o usuário tem a função necessária.
        """
        if not self.role_required:
            return True
        
        user = self.request.user
        
        # Superusuário sempre tem acesso
        if user.is_superuser:
            return True
        
        # Se account_required, verificar no contexto da conta
        if self.account_required:
            account = self.get_account()
            if not account:
                return False
            
            # Verificar se o usuário tem acesso à conta
            if not user.account_memberships.filter(account=account, status='active').exists():
                return False
            
            return user_has_role(user, self.role_required, account)
        else:
            return user_has_role(user, self.role_required)
    
    def get_account(self):
        """
        Obtém a conta do contexto da requisição.
        """
        account_id = (
            self.kwargs.get('account_id') or 
            self.request.GET.get('account_id') or
            self.request.session.get('current_account_id')
        )
        
        if not account_id:
            # Tentar obter da primeira conta do usuário
            membership = self.request.user.account_memberships.first()
            if membership:
                account_id = membership.account.id
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        return None
    
    def handle_no_permission(self):
        """
        Lida com a falta de função.
        """
        if self.request.headers.get('Content-Type') == 'application/json' or self.request.path.startswith('/api/'):
            return JsonResponse(
                {'error': f"Função '{self.role_required}' necessária"},
                status=403
            )
        
        if self.raise_exception:
            raise PermissionDenied(f"Função '{self.role_required}' necessária")
        
        return super().handle_no_permission()


class AccountMemberRequiredMixin(LoginRequiredMixin):
    """
    Mixin para verificar se o usuário é membro da conta.
    """
    raise_exception = True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.is_account_member():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def is_account_member(self):
        """
        Verifica se o usuário é membro da conta.
        """
        user = self.request.user
        
        # Superusuário sempre tem acesso
        if user.is_superuser:
            return True
        
        account = self.get_account()
        if not account:
            return False
        
        # Verificar se o usuário é membro da conta
        is_member = user.account_memberships.filter(
            account=account, 
            is_active=True
        ).exists()
        
        if is_member:
            # Adicionar a conta ao request para uso posterior
            self.request.current_account = account
        
        return is_member
    
    def get_account(self):
        """
        Obtém a conta do contexto da requisição.
        """
        account_id = (
            self.kwargs.get('account_id') or 
            self.request.GET.get('account_id') or
            self.request.session.get('current_account_id')
        )
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        return None
    
    def handle_no_permission(self):
        """
        Lida com a falta de acesso à conta.
        """
        if self.request.headers.get('Content-Type') == 'application/json' or self.request.path.startswith('/api/'):
            return JsonResponse(
                {'error': 'Usuário não é membro desta conta'},
                status=403
            )
        
        if self.raise_exception:
            raise PermissionDenied("Usuário não é membro desta conta")
        
        return super().handle_no_permission()


class MultiplePermissionsRequiredMixin(LoginRequiredMixin):
    """
    Mixin para verificar múltiplas permissões.
    """
    permissions_required = None  # Lista de permissões
    permissions_operator = 'AND'  # 'AND' ou 'OR'
    account_required = True
    raise_exception = True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permissions():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def has_permissions(self):
        """
        Verifica se o usuário tem as permissões necessárias.
        """
        if not self.permissions_required:
            return True
        
        user = self.request.user
        
        # Superusuário sempre tem acesso
        if user.is_superuser:
            return True
        
        account = None
        if self.account_required:
            account = self.get_account()
            if not account:
                return False
            
            # Verificar se o usuário tem acesso à conta
            if not user.account_memberships.filter(account=account, status='active').exists():
                return False
        
        # Verificar permissões
        permissions_check = []
        for permission_codename in self.permissions_required:
            try:
                permission = Permission.objects.get(
                    codename=permission_codename, 
                    is_active=True
                )
                has_perm = user_has_permission(user, permission, account)
                permissions_check.append(has_perm)
            except Permission.DoesNotExist:
                permissions_check.append(False)
        
        # Aplicar operador lógico
        if self.permissions_operator == 'OR':
            return any(permissions_check)
        else:  # AND
            return all(permissions_check)
    
    def get_account(self):
        """
        Obtém a conta do contexto da requisição.
        """
        account_id = (
            self.kwargs.get('account_id') or 
            self.request.GET.get('account_id') or
            self.request.session.get('current_account_id')
        )
        
        if not account_id:
            # Tentar obter da primeira conta do usuário
            membership = self.request.user.account_memberships.first()
            if membership:
                account_id = membership.account.id
        
        if account_id:
            try:
                return Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                pass
        
        return None
    
    def handle_no_permission(self):
        """
        Lida com a falta de permissões.
        """
        permissions_str = ', '.join(self.permissions_required)
        operator_str = 'todas as' if self.permissions_operator == 'AND' else 'uma das'
        
        if self.request.headers.get('Content-Type') == 'application/json' or self.request.path.startswith('/api/'):
            return JsonResponse(
                {'error': f"É necessário ter {operator_str} permissões: {permissions_str}"},
                status=403
            )
        
        if self.raise_exception:
            raise PermissionDenied(f"É necessário ter {operator_str} permissões: {permissions_str}")
        
        return super().handle_no_permission()


class PermissionContextMixin:
    """
    Mixin para adicionar contexto de permissões aos templates.
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            account = getattr(self.request, 'current_account', None)
            if not account:
                account = self.get_account() if hasattr(self, 'get_account') else None
            
            # Adicionar permissões do usuário ao contexto
            context['user_permissions'] = get_user_permissions(self.request.user, account)
            context['user_permission_codes'] = list(
                context['user_permissions'].values_list('codename', flat=True)
            )
            
            # Adicionar função para verificar permissões no template
            context['has_permission'] = lambda perm: user_has_permission(
                self.request.user, perm, account
            )
            
            # Adicionar função para verificar funções no template
            context['has_role'] = lambda role: user_has_role(
                self.request.user, role, account
            )
        
        return context