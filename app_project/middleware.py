from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class AdminRedirectMiddleware:
    """
    Middleware que redireciona usuários staff (superadmin) que tentam acessar
    URLs do user-panel para as URLs correspondentes do admin-panel
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se o usuário está autenticado e é staff
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path.startswith('/user-panel/')):
            
            logger.info(f"Staff user {request.user.username} trying to access {request.path}")
            
            # Mapear URLs do user-panel para admin-panel quando possível
            user_panel_to_admin_mapping = {
                '/user-panel/': '/admin-panel/',
                '/user-panel/social-networks/': '/admin-panel/',  # Redirecionar para dashboard admin
                '/user-panel/settings/': '/admin-panel/settings/general/',
                '/user-panel/accounts/': '/admin-panel/accounts/',
                '/user-panel/users/': '/admin-panel/users/',
                '/user-panel/sites/': '/admin-panel/sites/',
            }
            
            # Verificar se existe um mapeamento direto
            if request.path in user_panel_to_admin_mapping:
                redirect_url = user_panel_to_admin_mapping[request.path]
                logger.info(f"Redirecting staff user to {redirect_url}")
                return HttpResponseRedirect(redirect_url)
            
            # Para outras URLs do user-panel, redirecionar para o dashboard admin
            if request.path.startswith('/user-panel/'):
                logger.info(f"Redirecting staff user to admin dashboard")
                return HttpResponseRedirect('/admin-panel/')
        
        response = self.get_response(request)
        return response