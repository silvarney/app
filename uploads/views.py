import json
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from accounts.models import Account, AccountMembership
from .models import UploadedFile, ImageThumbnail, UploadQuota


@login_required
def file_list(request):
    """Lista todos os arquivos do usuário"""
    user = request.user
    search = request.GET.get('search', '')
    file_type = request.GET.get('type', '')
    account_filter = request.GET.get('account', '')
    
    # Contas do usuário
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__status='active'
    )
    
    # Query base - arquivos das contas do usuário
    files = UploadedFile.objects.filter(
        account__in=user_accounts
    ).select_related('account', 'uploaded_by')
    
    # Filtros
    if search:
        files = files.filter(
            Q(original_name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if file_type:
        files = files.filter(file_type=file_type)
    
    if account_filter:
        files = files.filter(account_id=account_filter)
    
    files = files.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(files, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_files = files.count()
    total_size = files.aggregate(total=Sum('file_size'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'file_type': file_type,
        'account': account_filter,
        'user_accounts': user_accounts,
        'file_type_choices': UploadedFile.FILE_TYPE_CHOICES,
        'total_files': total_files,
        'total_size': total_size,
    }
    
    return render(request, 'uploads/file_list.html', context)


@login_required
def file_upload(request):
    """Upload de arquivos"""
    user = request.user
    
    # Contas onde o usuário pode fazer upload
    user_accounts = Account.objects.filter(
        memberships__user=user,
        memberships__role__in=['owner', 'admin', 'editor'],
        memberships__status='active'
    )
    
    if not user_accounts.exists():
        messages.error(request, 'Você não tem permissão para fazer upload de arquivos.')
        return redirect('uploads:file_list')
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        account = get_object_or_404(user_accounts, id=account_id)
        
        # Verificar quota
        quota, created = UploadQuota.objects.get_or_create(account=account)
        if created:
            quota.save()
        
        # Resetar contador mensal se necessário
        quota.reset_monthly_counter()
        
        uploaded_files = []
        errors = []
        
        # Processar cada arquivo
        files = request.FILES.getlist('files')
        for file in files:
            # Verificar se pode fazer upload
            can_upload, error_msg = quota.can_upload_file(file.size)
            if not can_upload:
                errors.append(f"{file.name}: {error_msg}")
                continue
            
            try:
                # Detectar MIME type
                mime_type, _ = mimetypes.guess_type(file.name)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                
                # Criar arquivo
                uploaded_file = UploadedFile.objects.create(
                    account=account,
                    uploaded_by=user,
                    file=file,
                    original_name=file.name,
                    file_size=file.size,
                    mime_type=mime_type,
                    description=request.POST.get('description', ''),
                    alt_text=request.POST.get('alt_text', ''),
                    is_public=request.POST.get('is_public') == 'on'
                )
                
                # Atualizar quota
                quota.add_file_usage(file.size)
                
                # Criar thumbnail se for imagem
                if uploaded_file.is_image:
                    ImageThumbnail.create_thumbnail(uploaded_file, 'small')
                    ImageThumbnail.create_thumbnail(uploaded_file, 'medium')
                    ImageThumbnail.create_thumbnail(uploaded_file, 'large')
                
                uploaded_files.append(uploaded_file)
                
            except Exception as e:
                errors.append(f"{file.name}: Erro ao processar arquivo - {str(e)}")
        
        # Mensagens de resultado
        if uploaded_files:
            messages.success(request, f"{len(uploaded_files)} arquivo(s) enviado(s) com sucesso!")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': len(uploaded_files) > 0,
                'uploaded_count': len(uploaded_files),
                'errors': errors
            })
        
        return redirect('uploads:file_list')
    
    context = {
        'user_accounts': user_accounts,
    }
    
    return render(request, 'uploads/file_upload.html', context)


@login_required
def file_detail(request, file_id):
    """Detalhes do arquivo"""
    user = request.user
    
    # Verificar acesso
    file = get_object_or_404(
        UploadedFile,
        id=file_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    # Verificar permissão
    user_membership = AccountMembership.objects.get(
        account=file.account,
        user=user,
        status='active'
    )
    
    can_edit = user_membership.role in ['owner', 'admin', 'editor'] or file.uploaded_by == user
    can_delete = user_membership.role in ['owner', 'admin'] or file.uploaded_by == user
    
    # Thumbnails (se for imagem)
    thumbnails = file.thumbnails.all() if file.is_image else []
    
    context = {
        'file': file,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'thumbnails': thumbnails,
    }
    
    return render(request, 'uploads/file_detail.html', context)


@login_required
def file_edit(request, file_id):
    """Editar arquivo"""
    user = request.user
    
    # Verificar acesso e permissão
    file = get_object_or_404(
        UploadedFile,
        id=file_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    user_membership = AccountMembership.objects.get(
        account=file.account,
        user=user,
        status='active'
    )
    
    can_edit = user_membership.role in ['owner', 'admin', 'editor'] or file.uploaded_by == user
    
    if not can_edit:
        messages.error(request, 'Você não tem permissão para editar este arquivo.')
        return redirect('uploads:file_detail', file_id=file.id)
    
    if request.method == 'POST':
        # Atualizar metadados
        file.description = request.POST.get('description', file.description)
        file.alt_text = request.POST.get('alt_text', file.alt_text)
        file.is_public = request.POST.get('is_public') == 'on'
        file.save()
        
        messages.success(request, 'Arquivo atualizado com sucesso!')
        return redirect('uploads:file_detail', file_id=file.id)
    
    context = {
        'file': file,
    }
    
    return render(request, 'uploads/file_edit.html', context)


@login_required
@require_http_methods(["POST"])
def file_delete(request, file_id):
    """Deletar arquivo"""
    user = request.user
    
    # Verificar acesso e permissão
    file = get_object_or_404(
        UploadedFile,
        id=file_id,
        account__memberships__user=user,
        account__memberships__status='active'
    )
    
    user_membership = AccountMembership.objects.get(
        account=file.account,
        user=user,
        status='active'
    )
    
    can_delete = user_membership.role in ['owner', 'admin'] or file.uploaded_by == user
    
    if not can_delete:
        messages.error(request, 'Você não tem permissão para deletar este arquivo.')
        return redirect('uploads:file_detail', file_id=file.id)
    
    # Atualizar quota
    quota = UploadQuota.objects.get(account=file.account)
    quota.remove_file_usage(file.file_size)
    
    file_name = file.original_name
    
    # Deletar arquivo físico
    if file.file:
        try:
            default_storage.delete(file.file.name)
        except Exception:
            pass
    
    # Deletar thumbnails
    for thumbnail in file.thumbnails.all():
        if thumbnail.file:
            try:
                default_storage.delete(thumbnail.file.name)
            except Exception:
                pass
    
    file.delete()
    
    messages.success(request, f'Arquivo "{file_name}" deletado com sucesso!')
    return redirect('uploads:file_list')


@login_required
def file_serve(request, file_id):
    """Servir arquivo (com controle de acesso)"""
    user = request.user
    
    # Verificar acesso
    file = get_object_or_404(
        UploadedFile,
        id=file_id
    )
    
    # Verificar se é público ou se o usuário tem acesso
    if not file.is_public:
        # Verificar se o usuário tem acesso à conta
        has_access = AccountMembership.objects.filter(
            account=file.account,
            user=user,
            status='active'
        ).exists()
        
        if not has_access:
            raise Http404("Arquivo não encontrado")
    
    # Servir arquivo
    try:
        response = HttpResponse(
            file.file.read(),
            content_type=file.mime_type
        )
        response['Content-Disposition'] = f'inline; filename="{file.original_name}"'
        return response
    except Exception:
        raise Http404("Arquivo não encontrado")


@login_required
def thumbnail_serve(request, file_id, size):
    """Servir thumbnail"""
    user = request.user
    
    # Verificar acesso ao arquivo original
    file = get_object_or_404(
        UploadedFile,
        id=file_id
    )
    
    # Verificar se é público ou se o usuário tem acesso
    if not file.is_public:
        has_access = AccountMembership.objects.filter(
            account=file.account,
            user=user,
            status='active'
        ).exists()
        
        if not has_access:
            raise Http404("Thumbnail não encontrado")
    
    # Buscar thumbnail
    thumbnail = get_object_or_404(
        ImageThumbnail,
        original_file=file,
        size=size
    )
    
    # Servir thumbnail
    try:
        response = HttpResponse(
            thumbnail.file.read(),
            content_type='image/jpeg'
        )
        response['Content-Disposition'] = f'inline; filename="thumb_{size}_{file.original_name}"'
        return response
    except Exception:
        raise Http404("Thumbnail não encontrado")


@login_required
def quota_status(request):
    """Status da quota de upload"""
    user = request.user
    account_id = request.GET.get('account')
    
    if not account_id:
        return JsonResponse({'error': 'Account ID required'}, status=400)
    
    # Verificar acesso à conta
    account = get_object_or_404(
        Account,
        id=account_id,
        memberships__user=user,
        memberships__status='active'
    )
    
    # Obter quota
    quota, created = UploadQuota.objects.get_or_create(account=account)
    if created:
        quota.save()
    
    # Resetar contador mensal se necessário
    quota.reset_monthly_counter()
    
    return JsonResponse({
        'max_storage_mb': quota.max_storage_mb,
        'used_storage_mb': round(quota.used_storage_mb, 2),
        'storage_percentage': round(quota.storage_percentage, 1),
        'max_file_size_mb': quota.max_file_size_mb,
        'max_files_per_month': quota.max_files_per_month,
        'files_uploaded_this_month': quota.files_uploaded_this_month,
        'is_storage_full': quota.is_storage_full,
        'is_monthly_limit_reached': quota.is_monthly_limit_reached,
    })


@login_required
@csrf_exempt
def ajax_upload(request):
    """Upload via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    account_id = request.POST.get('account')
    
    if not account_id:
        return JsonResponse({'error': 'Account ID required'}, status=400)
    
    # Verificar acesso à conta
    try:
        account = Account.objects.get(
            id=account_id,
            memberships__user=user,
            memberships__role__in=['owner', 'admin', 'editor'],
            memberships__status='active'
        )
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Verificar quota
    quota, created = UploadQuota.objects.get_or_create(account=account)
    if created:
        quota.save()
    
    quota.reset_monthly_counter()
    
    # Processar arquivo
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # Verificar se pode fazer upload
    can_upload, error_msg = quota.can_upload_file(file.size)
    if not can_upload:
        return JsonResponse({'error': error_msg}, status=400)
    
    try:
        # Detectar MIME type
        mime_type, _ = mimetypes.guess_type(file.name)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Criar arquivo
        uploaded_file = UploadedFile.objects.create(
            account=account,
            uploaded_by=user,
            file=file,
            original_name=file.name,
            file_size=file.size,
            mime_type=mime_type,
            description=request.POST.get('description', ''),
            alt_text=request.POST.get('alt_text', ''),
            is_public=request.POST.get('is_public') == 'true'
        )
        
        # Atualizar quota
        quota.add_file_usage(file.size)
        
        # Criar thumbnails se for imagem
        thumbnails = {}
        if uploaded_file.is_image:
            for size in ['small', 'medium', 'large']:
                thumbnail = ImageThumbnail.create_thumbnail(uploaded_file, size)
                if thumbnail:
                    thumbnails[size] = {
                        'url': f'/uploads/thumbnail/{uploaded_file.id}/{size}/',
                        'width': thumbnail.width,
                        'height': thumbnail.height
                    }
        
        return JsonResponse({
            'success': True,
            'file': {
                'id': str(uploaded_file.id),
                'name': uploaded_file.original_name,
                'size': uploaded_file.file_size,
                'size_human': uploaded_file.file_size_human,
                'type': uploaded_file.file_type,
                'url': f'/uploads/file/{uploaded_file.id}/',
                'is_image': uploaded_file.is_image,
                'thumbnails': thumbnails,
                'created_at': uploaded_file.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)
