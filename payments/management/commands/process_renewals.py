from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.services import BillingService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process subscription renewals'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be renewed without actually renewing',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting renewal process at {timezone.now()}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual renewals will be processed')
            )
        
        try:
            if dry_run:
                # Simular o processo sem fazer alterações
                from datetime import timedelta
                from payments.models import Subscription
                
                tomorrow = timezone.now() + timedelta(days=1)
                expiring_subscriptions = Subscription.objects.filter(
                    current_period_end__date=tomorrow.date(),
                    auto_renew=True,
                    status__in=['active', 'trial']
                )
                
                count = expiring_subscriptions.count()
                self.stdout.write(
                    f'Would process {count} subscription renewals'
                )
                
                if verbose:
                    for subscription in expiring_subscriptions:
                        self.stdout.write(
                            f'  - Subscription {subscription.id} for account {subscription.account.name} '
                            f'(Plan: {subscription.plan.name})'
                        )
            else:
                # Processar renovações reais
                renewed_count = BillingService.process_renewals()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed {renewed_count} subscription renewals'
                    )
                )
                
        except Exception as e:
            logger.error(f'Error in renewal process: {str(e)}')
            self.stdout.write(
                self.style.ERROR(
                    f'Error processing renewals: {str(e)}'
                )
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS('Renewal process completed')
        )