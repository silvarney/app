from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import json

from .models import User
from accounts.models import Account


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
    return redirect('/')


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


def register_view(request):
    """View de registro de usuário"""
    if request.user.is_authenticated:
        # Redirecionar baseado no tipo de usuário
        if request.user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return redirect('user_panel:dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        company_name = request.POST.get('company_name')
        terms = request.POST.get('terms')
        newsletter = request.POST.get('newsletter')
        
        # Validações
        if not all([first_name, last_name, email, password1, password2]):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        elif password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        elif len(password1) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        elif not terms:
            messages.error(request, 'Você deve aceitar os termos de serviço.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Já existe um usuário com este email.')
        else:
            try:
                # Criar usuário
                user = User.objects.create_user(
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Criar conta padrão para o usuário
                account = Account.objects.create(
                    name=company_name or f"{first_name} {last_name}",
                    owner=user,
                    is_active=True
                )
                
                # Adicionar usuário à conta
                account.users.add(user)
                
                # Fazer login automático
                user = authenticate(request, username=email, password=password1)
                if user:
                    login(request, user)
                    messages.success(request, 'Conta criada com sucesso! Bem-vindo!')
                    return redirect('user_panel:dashboard')
                
            except Exception as e:
                messages.error(request, f'Erro ao criar conta: {str(e)}')
    
    return render(request, 'auth/register.html')


def password_reset_view(request):
    """View de solicitação de recuperação de senha"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                
                # Gerar token e UID
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Obter site atual
                current_site = get_current_site(request)
                
                # Criar link de recuperação
                reset_link = f"http://{current_site.domain}/auth/password-reset-confirm/{uid}/{token}/"
                
                # Preparar contexto do email
                context = {
                    'user': user,
                    'reset_link': reset_link,
                    'site_name': current_site.name,
                }
                
                # Renderizar template do email
                subject = 'Recuperação de Senha'
                message = render_to_string('auth/password_reset_email.txt', context)
                html_message = render_to_string('auth/password_reset_email.html', context)
                
                # Enviar email
                send_mail(
                    subject,
                    message,
                    'noreply@exemplo.com',
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                messages.success(request, 'Email de recuperação enviado com sucesso!')
                
            except User.DoesNotExist:
                # Por segurança, não revelar se o email existe ou não
                messages.success(request, 'Se o email existir, você receberá as instruções de recuperação.')
            except Exception as e:
                messages.error(request, 'Erro ao enviar email. Tente novamente mais tarde.')
        else:
            messages.error(request, 'Por favor, informe um email válido.')
    
    return render(request, 'auth/password_reset.html')


def password_reset_confirm_view(request, uidb64, token):
    """View de confirmação de recuperação de senha"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            
            if password1 and password2:
                if password1 == password2:
                    if len(password1) >= 8:
                        # Validar força da senha
                        has_lower = any(c.islower() for c in password1)
                        has_upper = any(c.isupper() for c in password1)
                        has_digit = any(c.isdigit() for c in password1)
                        
                        if has_lower and has_upper and has_digit:
                            user.set_password(password1)
                            user.save()
                            messages.success(request, 'Senha alterada com sucesso! Faça login com sua nova senha.')
                            return redirect('login')
                        else:
                            messages.error(request, 'A senha deve conter pelo menos uma letra minúscula, uma maiúscula e um número.')
                    else:
                        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
                else:
                    messages.error(request, 'As senhas não coincidem.')
            else:
                messages.error(request, 'Por favor, preencha todos os campos.')
    else:
        validlink = False
    
    context = {
        'validlink': validlink,
        'form': None,  # Para compatibilidade com templates Django padrão
    }
    
    return render(request, 'auth/password_reset_confirm.html', context)
