"""
URL configuration for saas_project project.

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
from django.shortcuts import redirect

def home_redirect(request):
    """Redireciona para o painel apropriado baseado no usuário"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return redirect('user_panel:dashboard')
    else:
        return redirect('/login/')

from users.views import login_view, logout_view, profile_view, register_view, password_reset_view, password_reset_confirm_view

urlpatterns = [
    path('', home_redirect, name='home'),
    path('django-admin/', admin.site.urls),  # Admin Django nativo
    path('login/', login_view, name='login'),         # Login direto
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
    path('sites/', include('site_management.urls')),  # Gerenciamento de Sites
    path('admin-panel/sites/', include('site_management.urls')),  # Gerenciamento de Sites (Admin)
]
