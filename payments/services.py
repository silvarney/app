from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from decimal import Decimal
import stripe
import logging
from datetime import timedelta

from .models import Plan, Subscription, Payment, Invoice
from accounts.models import Account

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
logger = logging.getLogger(__name__)


class SubscriptionService:
    """Serviço para gerenciar assinaturas"""
    
    @staticmethod
    def create_subscription(account, plan, trial_days=None):
        """Cria uma nova assinatura"""
        now = timezone.now()
        
        # Usar trial_days do parâmetro ou do plano
        trial_days = trial_days or plan.trial_days
        
        # Calcular datas
        trial_ends_at = None
        current_period_start = now
        
        if trial_days > 0:
            trial_ends_at = now + timedelta(days=trial_days)
            current_period_end = trial_ends_at
            status = 'trial'
        else:
            current_period_end = SubscriptionService._calculate_next_period_end(
                now, plan.billing_cycle
            )
            status = 'active' if plan.is_free else 'active'
        
        # Criar assinatura
        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=status,
            started_at=now,
            trial_ends_at=trial_ends_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            price_snapshot=plan.price
        )
        
        logger.info(f'Created subscription {subscription.id} for account {account.id}')
        return subscription
    
    @staticmethod
    def _calculate_next_period_end(start_date, billing_cycle):
        """Calcula a data de fim do próximo período"""
        if billing_cycle == 'monthly':
            return start_date + timedelta(days=30)
        elif billing_cycle == 'quarterly':
            return start_date + timedelta(days=90)
        elif billing_cycle == 'yearly':
            return start_date + timedelta(days=365)
        elif billing_cycle == 'lifetime':
            return start_date + timedelta(days=365 * 100)  # 100 anos
        else:
            return start_date + timedelta(days=30)
    
    @staticmethod
    def renew_subscription(subscription):
        """Renova uma assinatura"""
        if not subscription.auto_renew:
            logger.info(f'Subscription {subscription.id} not set for auto-renewal')
            return False
        
        # Calcular novo período
        new_period_start = subscription.current_period_end
        new_period_end = SubscriptionService._calculate_next_period_end(
            new_period_start, subscription.plan.billing_cycle
        )
        
        # Atualizar assinatura
        subscription.current_period_start = new_period_start
        subscription.current_period_end = new_period_end
        subscription.status = 'active'
        subscription.save()
        
        # Criar pagamento se não for gratuito
        if not subscription.plan.is_free:
            payment = PaymentService.create_payment(
                subscription=subscription,
                amount=subscription.plan.price,
                description=f'Renewal for {subscription.plan.name}'
            )
            
            # Tentar processar pagamento automaticamente
            PaymentService.process_automatic_payment(payment)
        
        logger.info(f'Renewed subscription {subscription.id}')
        return True
    
    @staticmethod
    def cancel_subscription(subscription, at_period_end=True, reason=None):
        """Cancela uma assinatura"""
        subscription.canceled_at = timezone.now()
        subscription.auto_renew = False
        
        if at_period_end:
            subscription.ends_at = subscription.current_period_end
        else:
            subscription.status = 'canceled'
            subscription.ends_at = timezone.now()
        
        if reason:
            subscription.metadata['cancellation_reason'] = reason
        
        subscription.save()
        
        # Enviar email de confirmação
        NotificationService.send_subscription_canceled_email(subscription)
        
        logger.info(f'Canceled subscription {subscription.id}')
        return subscription
    
    @staticmethod
    def upgrade_subscription(subscription, new_plan):
        """Faz upgrade de uma assinatura"""
        old_plan = subscription.plan
        
        # Calcular valor proporcional
        days_remaining = (subscription.current_period_end - timezone.now()).days
        old_daily_rate = subscription.price_snapshot / 30  # Assumindo ciclo mensal
        new_daily_rate = new_plan.price / 30
        
        credit_amount = old_daily_rate * days_remaining
        charge_amount = new_daily_rate * days_remaining
        difference = charge_amount - credit_amount
        
        # Atualizar assinatura
        subscription.plan = new_plan
        subscription.price_snapshot = new_plan.price
        subscription.metadata['upgrade_from'] = str(old_plan.id)
        subscription.metadata['upgrade_date'] = timezone.now().isoformat()
        subscription.save()
        
        # Criar pagamento para a diferença se necessário
        if difference > 0:
            payment = PaymentService.create_payment(
                subscription=subscription,
                amount=difference,
                description=f'Upgrade from {old_plan.name} to {new_plan.name}'
            )
            return subscription, payment
        
        logger.info(f'Upgraded subscription {subscription.id} from {old_plan.name} to {new_plan.name}')
        return subscription, None


class PaymentService:
    """Serviço para gerenciar pagamentos"""
    
    @staticmethod
    def create_payment(subscription, amount, description='', payment_method='stripe'):
        """Cria um novo pagamento"""
        payment = Payment.objects.create(
            subscription=subscription,
            amount=amount,
            currency='BRL',
            payment_method=payment_method,
            description=description,
            due_date=subscription.current_period_end
        )
        
        logger.info(f'Created payment {payment.id} for subscription {subscription.id}')
        return payment
    
    @staticmethod
    def create_stripe_payment_intent(payment):
        """Cria um Payment Intent no Stripe"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Stripe usa centavos
                currency=payment.currency.lower(),
                metadata={
                    'payment_id': str(payment.id),
                    'subscription_id': str(payment.subscription.id),
                    'account_id': str(payment.subscription.account.id)
                }
            )
            
            payment.gateway_transaction_id = intent.id
            payment.gateway_response = intent
            payment.save()
            
            return intent
        except Exception as e:
            logger.error(f'Error creating Stripe payment intent: {str(e)}')
            raise
    
    @staticmethod
    def process_automatic_payment(payment):
        """Processa pagamento automático (para renovações)"""
        # Implementar lógica de pagamento automático
        # Por exemplo, usando cartão salvo do cliente
        pass
    
    @staticmethod
    def handle_failed_payment(payment, reason=None):
        """Lida com falha no pagamento"""
        payment.mark_as_failed(reason)
        
        # Atualizar status da assinatura
        subscription = payment.subscription
        if subscription.status == 'active':
            subscription.status = 'past_due'
            subscription.save()
        
        # Enviar notificação
        NotificationService.send_payment_failed_email(payment)
        
        # Agendar nova tentativa se possível
        if payment.can_retry:
            # Implementar lógica de retry
            pass
        
        logger.info(f'Handled failed payment {payment.id}')


class NotificationService:
    """Serviço para envio de notificações"""
    
    @staticmethod
    def send_subscription_canceled_email(subscription):
        """Envia email de cancelamento de assinatura"""
        try:
            subject = 'Assinatura Cancelada'
            message = render_to_string('emails/subscription_canceled.html', {
                'subscription': subscription,
                'account': subscription.account
            })
            
            # Obter email do usuário principal da conta
            primary_user = subscription.account.users.filter(
                memberships__role='owner'
            ).first()
            
            if primary_user:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[primary_user.email],
                    fail_silently=False
                )
                
            logger.info(f'Sent cancellation email for subscription {subscription.id}')
        except Exception as e:
            logger.error(f'Error sending cancellation email: {str(e)}')
    
    @staticmethod
    def send_payment_failed_email(payment):
        """Envia email de falha no pagamento"""
        try:
            subject = 'Falha no Pagamento'
            message = render_to_string('emails/payment_failed.html', {
                'payment': payment,
                'subscription': payment.subscription,
                'account': payment.subscription.account
            })
            
            # Obter email do usuário principal da conta
            primary_user = payment.subscription.account.users.filter(
                memberships__role='owner'
            ).first()
            
            if primary_user:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[primary_user.email],
                    fail_silently=False
                )
                
            logger.info(f'Sent payment failed email for payment {payment.id}')
        except Exception as e:
            logger.error(f'Error sending payment failed email: {str(e)}')
    
    @staticmethod
    def send_renewal_reminder_email(subscription, days_until_renewal):
        """Envia lembrete de renovação"""
        try:
            subject = f'Sua assinatura será renovada em {days_until_renewal} dias'
            message = render_to_string('emails/renewal_reminder.html', {
                'subscription': subscription,
                'account': subscription.account,
                'days_until_renewal': days_until_renewal
            })
            
            # Obter email do usuário principal da conta
            primary_user = subscription.account.users.filter(
                memberships__role='owner'
            ).first()
            
            if primary_user:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[primary_user.email],
                    fail_silently=False
                )
                
            logger.info(f'Sent renewal reminder for subscription {subscription.id}')
        except Exception as e:
            logger.error(f'Error sending renewal reminder: {str(e)}')


class BillingService:
    """Serviço para gerenciar faturamento"""
    
    @staticmethod
    def generate_invoice(subscription, payment=None):
        """Gera uma fatura para a assinatura"""
        from django.utils import timezone
        
        # Calcular valores
        subtotal = subscription.price_snapshot
        tax_amount = Decimal('0.00')  # Implementar cálculo de impostos se necessário
        discount_amount = Decimal('0.00')  # Implementar descontos se necessário
        total = subtotal + tax_amount - discount_amount
        
        # Criar fatura
        invoice = Invoice.objects.create(
            subscription=subscription,
            payment=payment,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total=total,
            issue_date=timezone.now().date(),
            due_date=subscription.current_period_end.date(),
            description=f'Subscription to {subscription.plan.name}'
        )
        
        logger.info(f'Generated invoice {invoice.invoice_number} for subscription {subscription.id}')
        return invoice
    
    @staticmethod
    def process_renewals():
        """Processa renovações automáticas (para ser executado via cron/celery)"""
        # Buscar assinaturas que vencem em 1 dia
        tomorrow = timezone.now() + timedelta(days=1)
        expiring_subscriptions = Subscription.objects.filter(
            current_period_end__date=tomorrow.date(),
            auto_renew=True,
            status__in=['active', 'trial']
        )
        
        renewed_count = 0
        for subscription in expiring_subscriptions:
            try:
                if SubscriptionService.renew_subscription(subscription):
                    renewed_count += 1
            except Exception as e:
                logger.error(f'Error renewing subscription {subscription.id}: {str(e)}')
        
        logger.info(f'Processed {renewed_count} subscription renewals')
        return renewed_count
    
    @staticmethod
    def send_renewal_reminders():
        """Envia lembretes de renovação (para ser executado via cron/celery)"""
        # Enviar lembretes 7 dias antes
        reminder_date = timezone.now() + timedelta(days=7)
        subscriptions_to_remind = Subscription.objects.filter(
            current_period_end__date=reminder_date.date(),
            auto_renew=True,
            status__in=['active', 'trial']
        )
        
        sent_count = 0
        for subscription in subscriptions_to_remind:
            try:
                NotificationService.send_renewal_reminder_email(subscription, 7)
                sent_count += 1
            except Exception as e:
                logger.error(f'Error sending renewal reminder for subscription {subscription.id}: {str(e)}')
        
        logger.info(f'Sent {sent_count} renewal reminders')
        return sent_count