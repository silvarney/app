from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Account, AccountMembership


@receiver(post_save, sender=Account)
def create_owner_membership(sender, instance, created, **kwargs):
    """Cria automaticamente um membership de owner quando uma conta é criada"""
    if created:
        AccountMembership.objects.create(
            account=instance,
            user=instance.owner,
            role='owner',
            status='active',
            can_invite_users=True,
            can_manage_billing=True,
            can_manage_settings=True,
            can_view_analytics=True,
            joined_at=timezone.now()
        )
        
        # Define data de expiração do trial se não foi definida
        if not instance.trial_ends_at and instance.status == 'trial':
            instance.trial_ends_at = timezone.now() + timedelta(days=30)
            instance.save(update_fields=['trial_ends_at'])