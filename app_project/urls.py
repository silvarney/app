"""
URL configuration for app_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse
from django.db import connection

def home_redirect(request):
    """Redireciona para o painel apropriado baseado no usuário"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_panel:dashboard')
        else:
            return redirect('user_panel:dashboard')
    else:
        return redirect('/')

def health_check(request):
    """Endpoint de health check para Docker"""
    try:
        # Testa conexão com o banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'healthy', 'database': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)

from users.views import login_view, logout_view, profile_view, register_view, password_reset_view, password_reset_confirm_view

urlpatterns = [
    path('', login_view, name='home'),
    path('health/', health_check, name='health_check'),  # Health check para Docker
    path('admin/', admin.site.urls),  # Admin Django nativo
    path('django-admin/', admin.site.urls),  # Admin Django nativo (compatibilidade)
    # path('login/', login_view, name='login'),         # Login direto - REMOVIDO (login agora está na raiz)
    path('logout/', logout_view, name='logout'),      # Logout direto
    path('register/', register_view, name='register'), # Registro direto
    path('password-reset/', password_reset_view, name='password_reset'), # Recuperação de senha
    path('password-reset-confirm/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'), # Confirmação de recuperação
    path('profile/', profile_view, name='profile'),   # Profile direto
    path('auth/', include('users.urls')),             # Autenticação (manter compatibilidade)
    path('accounts/', include('allauth.urls')),       # Django Allauth URLs
    path('admin-panel/', include('admin_panel.urls')),  # Painel Admin customizado
    path('user-panel/', include('user_panel.urls')),  # Painel Usuários
    path('uploads/', include('uploads.urls')),        # Sistema de Upload
    path('api/', include('api.urls')),                # API REST
    path('api/settings/', include('settings.urls')),  # Configurações API
    path('payments/', include('payments.urls')),      # Pagamentos
    path('accounts-management/', include('accounts.urls')),  # Gerenciamento de Contas
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
