from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Account, AccountMembership, AccountInvitation
from django.forms import ModelForm
from django import forms

User = get_user_model()


class AccountForm(ModelForm):
    """Formulário para criação e edição de contas"""
    
    class Meta:
        model = Account
        fields = [
            'name', 'slug', 'description', 'company_name', 'email', 'cnpj', 'cpf',
            'website', 'phone', 'address_line1', 'address_line2', 
            'city', 'state', 'postal_code', 'country', 'plan'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'plan': forms.Select(attrs={'class': 'form-control'}),
        }


class MembershipForm(ModelForm):
    """Formulário para gerenciamento de membros"""
    
    class Meta:
        model = AccountMembership
        fields = [
            'role', 'can_invite_users', 'can_manage_billing', 
            'can_manage_settings', 'can_view_analytics'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'can_invite_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_billing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_analytics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvitationForm(forms.Form):
    """Formulário para convite de novos membros"""
    
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        label='Função',
        choices=AccountMembership.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    can_invite_users = forms.BooleanField(
        label='Pode Convidar Usuários',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_billing = forms.BooleanField(
        label='Pode Gerenciar Cobrança',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_settings = forms.BooleanField(
        label='Pode Gerenciar Configurações',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_view_analytics = forms.BooleanField(
        label='Pode Ver Análises',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


def check_account_permission(user, account, required_role='member'):
    """Verifica se o usuário tem permissão na conta"""
    if user.is_superuser:
        return True
    
    try:
        membership = AccountMembership.objects.get(account=account, user=user, status='active')
        if required_role == 'owner':
            return membership.is_owner
        elif required_role == 'admin':
            return membership.is_admin
        else:
            return True
    except AccountMembership.DoesNotExist:
        return False


@login_required
def account_list(request):
    """Lista as contas do usuário"""
    if request.user.is_superuser:
        accounts = Account.objects.all()
    else:
        accounts = Account.objects.filter(
            memberships__user=request.user,
            memberships__status='active'
        ).distinct()
    
    return render(request, 'accounts/list.html', {
        'accounts': accounts
    })


@login_required
def account_detail(request, account_id):
    """Detalhes da conta"""
    account = get_object_or_404(Account, id=account_id)
    
    if not check_account_permission(request.user, account):
        raise PermissionDenied("Você não tem permissão para acessar esta conta.")
    
    members = AccountMembership.objects.filter(
        account=account,
        status='active'
    ).select_related('user')
    
    return render(request, 'accounts/detail.html', {
        'account': account,
        'members': members,
        'can_manage': check_account_permission(request.user, account, 'admin')
    })


@login_required
def account_create(request):
    """Cria uma nova conta"""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Cria a conta
                account = form.save(commit=False)
                account.owner = request.user
                account.save()
                
                # Cria o membership do proprietário
                AccountMembership.objects.create(
                    account=account,
                    user=request.user,
                    role='owner',
                    status='active',
                    can_invite_users=True,
                    can_manage_billing=True,
                    can_manage_settings=True,
                    can_view_analytics=True,
                    joined_at=timezone.now()
                )
                
                messages.success(request, f'Conta "{account.name}" criada com sucesso!')
                return redirect('accounts:detail', account_id=account.id)
    else:
        form = AccountForm()
    
    return render(request, 'accounts/form.html', {
        'form': form,
        'title': 'Criar Nova Conta',
        'action': 'create'
    })


@login_required
def account_edit(request, account_id):
    """Edita uma conta existente"""
    account = get_object_or_404(Account, id=account_id)
    
    # Apenas proprietários e admins podem editar
    if not check_account_permission(request.user, account, 'admin'):
        raise PermissionDenied("Você não tem permissão para editar esta conta.")
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'Conta "{account.name}" atualizada com sucesso!')
            return redirect('accounts:detail', account_id=account.id)
    else:
        form = AccountForm(instance=account)
    
    return render(request, 'accounts/form.html', {
        'form': form,
        'account': account,
        'title': f'Editar Conta: {account.name}',
        'action': 'edit'
    })


@login_required
@require_http_methods(["POST"])
def account_delete(request, account_id):
    """Remove uma conta"""
    account = get_object_or_404(Account, id=account_id)
    
    # Apenas o proprietário pode deletar a conta
    if not check_account_permission(request.user, account, 'owner'):
        raise PermissionDenied("Apenas o proprietário pode deletar a conta.")
    
    account_name = account.name
    account.delete()
    
    messages.success(request, f'Conta "{account_name}" removida com sucesso!')
    return redirect('accounts:list')


@login_required
def member_invite(request, account_id):
    """Convida um novo membro para a conta"""
    account = get_object_or_404(Account, id=account_id)
    
    # Apenas admins e proprietários podem convidar
    if not check_account_permission(request.user, account, 'admin'):
        raise PermissionDenied("Você não tem permissão para convidar membros.")
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Verifica se já existe um membro com este email
            existing_member = AccountMembership.objects.filter(
                account=account,
                user__email=email
            ).first()
            
            if existing_member:
                messages.error(request, f'Usuário com email {email} já é membro desta conta.')
            else:
                # Verifica se já existe um convite pendente
                existing_invitation = AccountInvitation.objects.filter(
                    account=account,
                    email=email,
                    status='pending'
                ).first()
                
                if existing_invitation:
                    messages.error(request, f'Já existe um convite pendente para {email}.')
                else:
                    # Cria o convite
                    invitation = AccountInvitation.objects.create(
                        account=account,
                        email=email,
                        role=form.cleaned_data['role'],
                        can_invite_users=form.cleaned_data['can_invite_users'],
                        can_manage_billing=form.cleaned_data['can_manage_billing'],
                        can_manage_settings=form.cleaned_data['can_manage_settings'],
                        can_view_analytics=form.cleaned_data['can_view_analytics'],
                        invited_by=request.user
                    )
                    
                    # TODO: Enviar email de convite
                    
                    messages.success(request, f'Convite enviado para {email}!')
                    return redirect('accounts:detail', account_id=account.id)
    else:
        form = InvitationForm()
    
    return render(request, 'accounts/invite_member.html', {
        'form': form,
        'account': account
    })


@login_required
def member_edit(request, account_id, membership_id):
    """Edita um membro da conta"""
    account = get_object_or_404(Account, id=account_id)
    membership = get_object_or_404(AccountMembership, id=membership_id, account=account)
    
    # Apenas admins e proprietários podem editar membros
    if not check_account_permission(request.user, account, 'admin'):
        raise PermissionDenied("Você não tem permissão para editar membros.")
    
    # Não pode editar o proprietário
    if membership.is_owner:
        raise PermissionDenied("Não é possível editar o proprietário da conta.")
    
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, f'Membro {membership.user.get_full_name() or membership.user.username} atualizado com sucesso!')
            return redirect('accounts:detail', account_id=account.id)
    else:
        form = MembershipForm(instance=membership)
    
    return render(request, 'accounts/edit_member.html', {
        'form': form,
        'account': account,
        'membership': membership
    })


@login_required
@require_http_methods(["POST"])
def member_remove(request, account_id, membership_id):
    """Remove um membro da conta"""
    account = get_object_or_404(Account, id=account_id)
    membership = get_object_or_404(AccountMembership, id=membership_id, account=account)
    
    # Apenas admins e proprietários podem remover membros
    if not check_account_permission(request.user, account, 'admin'):
        raise PermissionDenied("Você não tem permissão para remover membros.")
    
    # Não pode remover o proprietário
    if membership.is_owner:
        raise PermissionDenied("Não é possível remover o proprietário da conta.")
    
    # Não pode se remover
    if membership.user == request.user:
        raise PermissionDenied("Você não pode se remover da conta.")
    
    member_name = membership.user.get_full_name() or membership.user.username
    membership.delete()
    
    messages.success(request, f'Membro {member_name} removido da conta com sucesso!')
    return redirect('accounts:detail', account_id=account.id)


@login_required
def invitation_accept(request, token):
    """Aceita um convite para se juntar a uma conta"""
    invitation = get_object_or_404(AccountInvitation, token=token)
    
    if not invitation.is_pending:
        messages.error(request, 'Este convite não está mais válido.')
        return redirect('accounts:list')
    
    if request.method == 'POST':
        try:
            membership = invitation.accept(request.user)
            messages.success(request, f'Você se juntou à conta "{invitation.account.name}" com sucesso!')
            return redirect('accounts:detail', account_id=invitation.account.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('accounts:list')
    
    return render(request, 'accounts/accept_invitation.html', {
        'invitation': invitation
    })


@login_required
@require_http_methods(["POST"])
def invitation_decline(request, token):
    """Recusa um convite"""
    invitation = get_object_or_404(AccountInvitation, token=token)
    
    if not invitation.is_pending:
        messages.error(request, 'Este convite não está mais válido.')
        return redirect('accounts:list')
    
    invitation.decline()
    messages.info(request, f'Convite para a conta "{invitation.account.name}" recusado.')
    return redirect('accounts:list')


@login_required
@require_http_methods(["POST"])
def invitation_cancel(request, account_id, invitation_id):
    """Cancela um convite"""
    account = get_object_or_404(Account, id=account_id)
    invitation = get_object_or_404(AccountInvitation, id=invitation_id, account=account)
    
    # Apenas admins e proprietários podem cancelar convites
    if not check_account_permission(request.user, account, 'admin'):
        raise PermissionDenied("Você não tem permissão para cancelar convites.")
    
    invitation.cancel()
    messages.success(request, f'Convite para {invitation.email} cancelado com sucesso!')
    return redirect('accounts:detail', account_id=account.id)


@login_required
def member_leave(request, account_id):
    """Permite que um membro saia da conta"""
    account = get_object_or_404(Account, id=account_id)
    
    try:
        membership = AccountMembership.objects.get(
            account=account,
            user=request.user,
            status='active'
        )
    except AccountMembership.DoesNotExist:
        raise Http404("Você não é membro desta conta.")
    
    # Proprietário não pode sair da própria conta
    if membership.is_owner:
        raise PermissionDenied("O proprietário não pode sair da própria conta.")
    
    if request.method == 'POST':
        account_name = account.name
        membership.delete()
        messages.success(request, f'Você saiu da conta "{account_name}" com sucesso!')
        return redirect('accounts:list')
    
    return render(request, 'accounts/leave_account.html', {
        'account': account,
        'membership': membership
    })
