from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import stripe
import json
import logging
from decimal import Decimal

from .models import Plan, Subscription, Payment, Invoice
from accounts.models import Account
from permissions.decorators import user_has_permission

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
logger = logging.getLogger(__name__)


class StripeWebhookView(View):
    """View para processar webhooks do Stripe"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error('Invalid payload in Stripe webhook')
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error('Invalid signature in Stripe webhook')
            return HttpResponse(status=400)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            self._handle_payment_failed(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self._handle_invoice_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            self._handle_invoice_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_deleted(event['data']['object'])
        else:
            logger.info(f'Unhandled Stripe event type: {event["type"]}')
        
        return HttpResponse(status=200)
    
    def _handle_payment_succeeded(self, payment_intent):
        """Processa pagamento bem-sucedido"""
        try:
            payment = Payment.objects.get(
                gateway_transaction_id=payment_intent['id']
            )
            payment.mark_as_paid()
            payment.gateway_response = payment_intent
            payment.save()
            
            # Atualizar assinatura se necessário
            if payment.subscription.status in ['past_due', 'trial']:
                payment.subscription.status = 'active'
                payment.subscription.save()
                
            logger.info(f'Payment {payment.id} marked as paid')
        except Payment.DoesNotExist:
            logger.error(f'Payment not found for transaction {payment_intent["id"]}')
    
    def _handle_payment_failed(self, payment_intent):
        """Processa falha no pagamento"""
        try:
            payment = Payment.objects.get(
                gateway_transaction_id=payment_intent['id']
            )
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            payment.mark_as_failed(failure_reason)
            payment.gateway_response = payment_intent
            payment.save()
            
            logger.info(f'Payment {payment.id} marked as failed: {failure_reason}')
        except Payment.DoesNotExist:
            logger.error(f'Payment not found for transaction {payment_intent["id"]}')
    
    def _handle_invoice_payment_succeeded(self, invoice):
        """Processa pagamento de fatura bem-sucedido"""
        # Implementar lógica específica para faturas
        pass
    
    def _handle_invoice_payment_failed(self, invoice):
        """Processa falha no pagamento de fatura"""
        # Implementar lógica específica para faturas
        pass
    
    def _handle_subscription_updated(self, subscription):
        """Processa atualização de assinatura"""
        # Implementar lógica de sincronização de assinatura
        pass
    
    def _handle_subscription_deleted(self, subscription):
        """Processa cancelamento de assinatura"""
        # Implementar lógica de cancelamento
        pass


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Cria um Payment Intent no Stripe"""
    try:
        data = request.data
        subscription_id = data.get('subscription_id')
        amount = data.get('amount')
        currency = data.get('currency', 'brl')
        
        if not subscription_id or not amount:
            return Response(
                {'error': 'subscription_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se o usuário tem acesso à assinatura
        subscription = get_object_or_404(
            Subscription,
            id=subscription_id,
            account=request.user.account
        )
        
        # Criar Payment Intent no Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(float(amount) * 100),  # Stripe usa centavos
            currency=currency,
            metadata={
                'subscription_id': str(subscription.id),
                'account_id': str(subscription.account.id)
            }
        )
        
        # Criar registro de pagamento local
        payment = Payment.objects.create(
            subscription=subscription,
            amount=Decimal(str(amount)),
            currency=currency.upper(),
            payment_method='stripe',
            gateway_transaction_id=intent.id,
            gateway_response=intent,
            description=f'Payment for {subscription.plan.name}'
        )
        
        return Response({
            'client_secret': intent.client_secret,
            'payment_id': payment.id
        })
        
    except Exception as e:
        logger.error(f'Error creating payment intent: {str(e)}')
        return Response(
            {'error': 'Failed to create payment intent'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    """Confirma um pagamento"""
    try:
        data = request.data
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return Response(
                {'error': 'payment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment = get_object_or_404(
            Payment,
            id=payment_id,
            subscription__account=request.user.account
        )
        
        # Verificar status no Stripe
        intent = stripe.PaymentIntent.retrieve(payment.gateway_transaction_id)
        
        if intent.status == 'succeeded':
            payment.mark_as_paid()
            payment.gateway_response = intent
            payment.save()
            
            # Atualizar assinatura
            if payment.subscription.status in ['past_due', 'trial']:
                payment.subscription.status = 'active'
                payment.subscription.save()
            
            return Response({'status': 'success', 'payment': {
                'id': payment.id,
                'status': payment.status,
                'amount': payment.amount
            }})
        else:
            return Response({
                'status': 'pending',
                'stripe_status': intent.status
            })
            
    except Exception as e:
        logger.error(f'Error confirming payment: {str(e)}')
        return Response(
            {'error': 'Failed to confirm payment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    """Cria uma nova assinatura"""
    try:
        data = request.data
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        account = request.user.account
        
        # Verificar se já existe uma assinatura ativa
        existing_subscription = Subscription.objects.filter(
            account=account,
            status__in=['active', 'trial']
        ).first()
        
        if existing_subscription:
            return Response(
                {'error': 'Account already has an active subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular datas
        now = timezone.now()
        trial_ends_at = None
        current_period_start = now
        
        if plan.trial_days > 0:
            trial_ends_at = now + timezone.timedelta(days=plan.trial_days)
            current_period_end = trial_ends_at
            subscription_status = 'trial'
        else:
            # Calcular próximo período baseado no ciclo de cobrança
            if plan.billing_cycle == 'monthly':
                current_period_end = now + timezone.timedelta(days=30)
            elif plan.billing_cycle == 'quarterly':
                current_period_end = now + timezone.timedelta(days=90)
            elif plan.billing_cycle == 'yearly':
                current_period_end = now + timezone.timedelta(days=365)
            else:
                current_period_end = now + timezone.timedelta(days=30)
            
            subscription_status = 'active' if plan.is_free else 'active'
        
        # Criar assinatura
        subscription = Subscription.objects.create(
            account=account,
            plan=plan,
            status=subscription_status,
            started_at=now,
            trial_ends_at=trial_ends_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            price_snapshot=plan.price
        )
        
        # Se não é gratuito e não está em trial, criar pagamento
        if not plan.is_free and subscription_status != 'trial':
            payment = Payment.objects.create(
                subscription=subscription,
                amount=plan.price,
                currency='BRL',
                payment_method='stripe',
                description=f'Subscription to {plan.name}',
                due_date=current_period_end
            )
            
            return Response({
                'subscription_id': subscription.id,
                'status': subscription.status,
                'requires_payment': True,
                'payment_id': payment.id
            })
        
        return Response({
            'subscription_id': subscription.id,
            'status': subscription.status,
            'requires_payment': False
        })
        
    except Exception as e:
        logger.error(f'Error creating subscription: {str(e)}')
        return Response(
            {'error': 'Failed to create subscription'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancela uma assinatura"""
    try:
        data = request.data
        subscription_id = data.get('subscription_id')
        at_period_end = data.get('at_period_end', True)
        
        if not subscription_id:
            return Response(
                {'error': 'subscription_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription = get_object_or_404(
            Subscription,
            id=subscription_id,
            account=request.user.account
        )
        
        if subscription.status == 'canceled':
            return Response(
                {'error': 'Subscription is already canceled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.cancel(at_period_end=at_period_end)
        
        return Response({
            'subscription_id': subscription.id,
            'status': subscription.status,
            'canceled_at': subscription.canceled_at,
            'ends_at': subscription.ends_at
        })
        
    except Exception as e:
        logger.error(f'Error canceling subscription: {str(e)}')
        return Response(
            {'error': 'Failed to cancel subscription'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
