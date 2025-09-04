from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'permissions', views.PermissionViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'plans', views.PlanViewSet)
router.register(r'subscriptions', views.SubscriptionViewSet)
router.register(r'payments', views.PaymentViewSet)

# Content Management
router.register(r'categories', views.CategoryViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'content', views.ContentViewSet)
router.register(r'content-attachments', views.ContentAttachmentViewSet)

# Domain Management
router.register(r'domains', views.DomainViewSet)
router.register(r'domain-configurations', views.DomainConfigurationViewSet)

app_name = 'api'

urlpatterns = [
    # Incluir rotas do router
    path('', include(router.urls)),
    
    # Autenticação
    path('auth/login/', views.LoginAPIView.as_view(), name='login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('auth/profile/', views.ProfileAPIView.as_view(), name='profile'),
    path('auth/password-reset/', views.PasswordResetAPIView.as_view(), name='password_reset'),
    path('auth/password-reset-confirm/', views.PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('auth/password-change/', views.PasswordChangeAPIView.as_view(), name='password_change'),
    
    # Gerenciamento de Contas
    path('accounts/switch/', views.SwitchAccountAPIView.as_view(), name='switch_account'),
    path('accounts/invite/', views.InviteUserAPIView.as_view(), name='invite_user'),
    path('accounts/members/', views.AccountMembersAPIView.as_view(), name='account_members'),
    
    # Permissões e Roles
    path('permissions/check/', views.CheckPermissionAPIView.as_view(), name='check_permission'),
    path('roles/assign/', views.AssignRoleAPIView.as_view(), name='assign_role'),
    path('roles/revoke/', views.RevokeRoleAPIView.as_view(), name='revoke_role'),
    
    # Faturamento e Assinaturas
    path('billing/checkout/', views.CreateCheckoutSessionAPIView.as_view(), name='create_checkout'),
    path('billing/webhook/', views.StripeWebhookAPIView.as_view(), name='stripe_webhook'),
    path('billing/cancel/', views.CancelSubscriptionAPIView.as_view(), name='cancel_subscription'),
    path('billing/payment-method/', views.UpdatePaymentMethodAPIView.as_view(), name='update_payment_method'),
    
    # Analytics e Relatórios
    path('analytics/dashboard/', views.DashboardAnalyticsAPIView.as_view(), name='dashboard_analytics'),
    path('analytics/usage/', views.UsageAnalyticsAPIView.as_view(), name='usage_analytics'),
    path('reports/export/', views.ExportReportAPIView.as_view(), name='export_report'),
    
    # Gerenciamento de Chaves API
    path('api-keys/', views.APIKeyListCreateAPIView.as_view(), name='api_keys'),
    path('api-keys/<int:pk>/', views.APIKeyDetailAPIView.as_view(), name='api_key_detail'),
    
    # Health Check
    path('health/', views.HealthCheckAPIView.as_view(), name='health_check'),
]