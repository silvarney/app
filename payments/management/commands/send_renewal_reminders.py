from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.services import BillingService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send renewal reminders to subscribers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days before renewal to send reminder (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what reminders would be sent without actually sending them',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting renewal reminder process at {timezone.now()}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual emails will be sent')
            )
        
        self.stdout.write(f'Sending reminders {days} days before renewal')
        
        try:
            if dry_run:
                # Simular o processo sem enviar emails
                from datetime import timedelta
                from payments.models import Subscription
                
                reminder_date = timezone.now() + timedelta(days=days)
                subscriptions_to_remind = Subscription.objects.filter(
                    current_period_end__date=reminder_date.date(),
                    auto_renew=True,
                    status__in=['active', 'trial']
                )
                
                count = subscriptions_to_remind.count()
                self.stdout.write(
                    f'Would send {count} renewal reminders'
                )
                
                if verbose:
                    for subscription in subscriptions_to_remind:
                        # Obter email do usuário principal
                        primary_user = subscription.account.users.filter(
                            memberships__role='owner'
                        ).first()
                        
                        email = primary_user.email if primary_user else 'No owner found'
                        
                        self.stdout.write(
                            f'  - Subscription {subscription.id} for account {subscription.account.name} '
                            f'(Plan: {subscription.plan.name}, Email: {email})'
                        )
            else:
                # Enviar lembretes reais
                if days == 7:
                    sent_count = BillingService.send_renewal_reminders()
                else:
                    # Implementar lógica personalizada para outros dias
                    from datetime import timedelta
                    from payments.models import Subscription
                    from payments.services import NotificationService
                    
                    reminder_date = timezone.now() + timedelta(days=days)
                    subscriptions_to_remind = Subscription.objects.filter(
                        current_period_end__date=reminder_date.date(),
                        auto_renew=True,
                        status__in=['active', 'trial']
                    )
                    
                    sent_count = 0
                    for subscription in subscriptions_to_remind:
                        try:
                            NotificationService.send_renewal_reminder_email(subscription, days)
                            sent_count += 1
                        except Exception as e:
                            logger.error(f'Error sending reminder for subscription {subscription.id}: {str(e)}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent {sent_count} renewal reminders'
                    )
                )
                
        except Exception as e:
            logger.error(f'Error in renewal reminder process: {str(e)}')
            self.stdout.write(
                self.style.ERROR(
                    f'Error sending renewal reminders: {str(e)}'
                )
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS('Renewal reminder process completed')
        )