from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Stripe webhook
    path('webhook/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    
    # Payment API endpoints
    path('api/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('api/confirm-payment/', views.confirm_payment, name='confirm_payment'),
    
    # Subscription API endpoints
    path('api/create-subscription/', views.create_subscription, name='create_subscription'),
    path('api/cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
]