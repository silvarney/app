from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import User


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
    
    return render(request, 'auth/login.html', context)


def logout_view(request):
    """View de logout"""
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('/login/')


@login_required
def profile_view(request):
    """View do perfil do usuário"""
    user = request.user
    
    if request.method == 'POST':
        # Atualizar dados do perfil
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        
        # Avatar
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('users:profile')
    
    context = {
        'user': user
    }
    
    return render(request, 'auth/profile.html', context)
