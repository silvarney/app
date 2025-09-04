from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


class PermissionDeniedMiddleware:
    """
    Middleware para interceptar exceções PermissionDenied e redirecionar
    para o dashboard apropriado em vez de para a página de login.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Processa exceções PermissionDenied.
        """
        if isinstance(exception, PermissionDenied):
            # Para requisições AJAX/API, retornar JSON
            if (request.headers.get('Content-Type') == 'application/json' or 
                request.path.startswith('/api/') or 
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
                return JsonResponse(
                    {'error': str(exception) or 'Permissão negada'},
                    status=403
                )
            
            # Para usuários autenticados
            if request.user.is_authenticated:
                # Se é uma requisição para submenus de configurações do admin, 
                # não redirecionar para evitar recarregamento da página
                if (request.path.startswith('/admin/settings/') and 
                    request.user.is_staff):
                    # Retornar uma resposta 403 com mensagem de erro
                    from django.http import HttpResponseForbidden
                    from django.template import loader
                    
                    template = loader.get_template('403.html')
                    context = {
                        'exception': str(exception) or 'Você não tem permissão para acessar esta funcionalidade.',
                        'request': request,
                    }
                    return HttpResponseForbidden(template.render(context, request))
                
                # Para outras páginas, redirecionar para dashboard apropriado
                if request.user.is_staff:
                    return redirect('admin_panel:dashboard')
                else:
                    return redirect('user_panel:dashboard')
            
            # Para usuários não autenticados, deixar o Django lidar normalmente
            # (redirecionará para LOGIN_URL)
            return None
        
        return None