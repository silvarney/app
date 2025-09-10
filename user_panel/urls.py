from django.urls import path, include
from . import views

app_name = 'user_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Contas
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/<uuid:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<uuid:account_id>/settings/', views.account_settings, name='account_settings'),
    path('accounts/<uuid:account_id>/leave/', views.leave_account, name='leave_account'),
    path('accounts/<uuid:account_id>/switch/', views.switch_account, name='switch_account'),
    
    # Perfil
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    
    # Configurações
    path('settings/', views.settings, name='settings'),
    
    # Funcionalidades extras
    path('notifications/', views.notifications, name='notifications'),
    path('activity/', views.activity_log, name='activity_log'),
    path('analytics/', views.user_analytics, name='user_analytics'),
    path('export/', views.export_data, name='export_data'),
    
    # Ações rápidas
    path('invite-user/', views.invite_user, name='invite_user'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('subscription/manage/', views.subscription_manage, name='subscription_manage'),
    

    
    # Membros
    path('members/', views.members_list, name='members_list'),
    path('members/invite/', views.invite_member, name='invite_member'),
    path('members/<uuid:membership_id>/edit/', views.edit_member, name='edit_member'),
    path('members/<uuid:membership_id>/remove/', views.remove_member, name='remove_member'),
    
    # Relatórios
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/accounts/', views.reports_accounts, name='reports_accounts'),
    path('reports/members/', views.reports_members, name='reports_members'),
    path('reports/activity/', views.reports_activity, name='reports_activity'),
    path('reports/export/', views.reports_export, name='reports_export'),
    
    # Itens
    path('items/', views.items_list, name='items_list'),
    path('items/create/', views.items_create, name='items_create'),
    path('items/<int:item_id>/edit/', views.items_edit, name='items_edit'),
    path('items/<int:item_id>/delete/', views.items_delete, name='items_delete'),
    
    # Tipos de Planos
    path('plan-types/', views.plan_types_list, name='plan_types_list'),
    path('plan-types/create/', views.plan_types_create, name='plan_types_create'),
    path('plan-types/<int:plan_type_id>/edit/', views.plan_types_edit, name='plan_types_edit'),
    path('plan-types/<int:plan_type_id>/delete/', views.plan_types_delete, name='plan_types_delete'),
    
    # Itens da Assinatura
    path('subscription-items/', views.subscription_items_list, name='subscription_items_list'),
    path('subscription-items/create/', views.subscription_items_create, name='subscription_items_create'),
    path('subscription-items/<int:item_id>/edit/', views.subscription_items_edit, name='subscription_items_edit'),
    path('subscription-items/<int:item_id>/delete/', views.subscription_items_delete, name='subscription_items_delete'),
    
    # Assinaturas
    path('subscriptions/', views.subscriptions_list, name='subscriptions_list'),
    path('subscriptions/create/', views.subscriptions_create, name='subscriptions_create'),
    path('subscriptions/<int:subscription_id>/edit/', views.subscriptions_edit, name='subscriptions_edit'),
    path('subscriptions/<int:subscription_id>/delete/', views.subscriptions_delete, name='subscriptions_delete'),
    
    # Pagamentos
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/create/', views.payments_create, name='payments_create'),
    path('payments/<int:payment_id>/edit/', views.payments_edit, name='payments_edit'),
    path('payments/<int:payment_id>/delete/', views.payments_delete, name='payments_delete'),
    
    # Extratos
    path('extracts/', views.extracts_list, name='extracts_list'),
    path('extracts/<int:extract_id>/', views.extract_detail, name='extract_detail'),
    path('extracts/export/', views.extracts_export, name='extracts_export'),
    
    # Bio
    path('bio/', views.bio_list, name='bio_list'),
    path('bio/create/', views.bio_create, name='bio_create'),
    path('bio/<int:bio_id>/edit/', views.bio_edit, name='bio_edit'),
    path('bio/<int:bio_id>/delete/', views.bio_delete, name='bio_delete'),
    
    # Categorias
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.categories_create, name='categories_create'),
    path('categories/<int:category_id>/edit/', views.categories_edit, name='categories_edit'),
    path('categories/<int:category_id>/delete/', views.categories_delete, name='categories_delete'),
    
    # Serviços
    path('services/', views.services_list, name='services_list'),
    path('services/create/', views.services_create, name='services_create'),
    path('services/<int:service_id>/edit/', views.services_edit, name='services_edit'),
    path('services/<int:service_id>/delete/', views.services_delete, name='services_delete'),
    
    # Redes Sociais
    path('social-networks/', views.social_networks_list, name='social_networks_list'),
    path('social-networks/create/', views.social_networks_create, name='social_networks_create'),
    path('social-networks/<int:network_id>/edit/', views.social_networks_edit, name='social_networks_edit'),
    path('social-networks/<int:network_id>/delete/', views.social_networks_delete, name='social_networks_delete'),
    
    # CTA
    path('cta/', views.cta_list, name='cta_list'),
    path('cta/create/', views.cta_create, name='cta_create'),
    path('cta/<int:cta_id>/edit/', views.cta_edit, name='cta_edit'),
    path('cta/<int:cta_id>/delete/', views.cta_delete, name='cta_delete'),
    
    # Blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<int:post_id>/edit/', views.blog_edit, name='blog_edit'),
    path('blog/<int:post_id>/delete/', views.blog_delete, name='blog_delete'),
    
    # Banners
    path('banners/', views.banners_list, name='banners_list'),
    path('banners/create/', views.banners_create, name='banners_create'),
    path('banners/<int:banner_id>/edit/', views.banners_edit, name='banners_edit'),
    path('banners/<int:banner_id>/delete/', views.banners_delete, name='banners_delete'),
    
    # Gerenciamento de Sites - Views diretas para evitar conflitos de namespace
    path('sites/', views.sites_list, name='sites_list'),
    path('sites/create/', views.site_create, name='site_create'),
    path('sites/<uuid:site_id>/', views.site_detail, name='site_detail'),
]