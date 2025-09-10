from settings.models import GlobalSetting
from accounts.models import AccountMembership

def appearance_settings(request):
    """
    Context processor para carregar configurações de aparência globalmente
    """
    try:
        # Buscar configurações de aparência
        primary_color = GlobalSetting.objects.filter(key='primary_color').first()
        secondary_color = GlobalSetting.objects.filter(key='secondary_color').first()
        
        return {
            'global_primary_color': primary_color.value if primary_color else '#3B82F6',
            'global_secondary_color': secondary_color.value if secondary_color else '#6B7280',
        }
    except Exception:
        # Valores padrão em caso de erro
        return {
            'global_primary_color': '#3B82F6',
            'global_secondary_color': '#6B7280',
        }

def user_context(request):
    """
    Context processor para carregar informações do usuário globalmente
    """
    context = {}
    
    if request.user.is_authenticated:
        # Verificar se o usuário pode gerenciar contas
        can_manage_account = False
        current_account = None
        
        try:
            # Buscar membership ativo do usuário
            account_membership = AccountMembership.objects.filter(
                user=request.user,
                status='active'
            ).select_related('account').first()
            
            if account_membership:
                current_account = account_membership.account
                can_manage_account = account_membership.role in ['owner', 'admin']
                
        except Exception:
            pass
        
        context.update({
            'can_manage_account': can_manage_account,
            'current_account': current_account,
        })
    
    return context