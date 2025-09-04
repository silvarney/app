from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import User, UserProfile


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    """Atribui automaticamente a função 'Usuário Padrão' para novos usuários"""
    if created:
        from permissions.models import Role, UserRole
        
        try:
            # Busca a função 'Usuário Padrão' (criada pelos signals de permissions)
            default_role = Role.objects.get(codename='standard_user')
            
            # Cria a associação UserRole para o novo usuário
            UserRole.objects.get_or_create(
                user=instance,
                role=default_role,
                account=None,  # Role de sistema, não específica de conta
                defaults={
                    'status': 'active',
                    'assigned_by': None  # Atribuição automática do sistema
                }
            )
        except Role.DoesNotExist:
            # Se a função não existir, não faz nada (será criada pelos comandos de populate)
            pass


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil quando um usuário é criado"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil do usuário quando o usuário é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_default_account(sender, instance, created, **kwargs):
    """Cria automaticamente uma conta padrão quando um usuário é criado"""
    if created:
        from accounts.models import Account
        
        # Cria um slug único baseado no nome do usuário
        base_slug = slugify(f"{instance.first_name}-{instance.last_name}" if instance.first_name and instance.last_name else instance.username)
        slug = base_slug
        counter = 1
        
        # Garante que o slug seja único
        while Account.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Cria a conta padrão
        account_name = f"Conta de {instance.get_full_name()}" if instance.get_full_name() else f"Conta de {instance.username}"
        
        Account.objects.create(
            name=account_name,
            slug=slug,
            description=f"Conta pessoal de {instance.get_full_name() or instance.username}",
            owner=instance,
            status='trial'
        )