"""
Arquivo temporário de URLs para desenvolvimento 
Usado apenas para testes iniciais
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.conf import settings
from django.conf.urls.static import static

def login_view(request):
    """View de login personalizada"""
    if request.user.is_authenticated:
        # Redirecionar baseado no tipo de usuário
        if request.user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return redirect('user_panel:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Determinar redirecionamento
                    if next_url:
                        return redirect(next_url)
                    elif user.is_staff:
                        return redirect('admin_panel:dashboard')
                    else:
                        return redirect('user_panel:dashboard')
                else:
                    messages.error(request, 'Sua conta está desativada.')
            else:
                messages.error(request, 'Email ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
    
    next_url = request.GET.get('next', '')
    context = {
        'next': next_url
    }
    
    return render(request, 'auth/login_simple.html', context)

@login_required
def dashboard_view(request):
    """View de dashboard temporária"""
    return render(request, 'dashboard.html', {
        'user': request.user
    })

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/')

# Define as rotas básicas para o funcionamento do sistema
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    
    # Adicionando as rotas dos outros apps necessários para o funcionamento
    path('admin-panel/', include('admin_panel.urls')),
    path('user-panel/', include('user_panel.urls')),
]

# Adiciona as rotas de mídia e arquivos estáticos se estivermos em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
