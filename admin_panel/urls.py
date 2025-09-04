from django.urls import path, include
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Redirecionamento para login
    path('login/', views.admin_login_redirect, name='admin_login_redirect'),
    
    # Usuários
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/check-accounts/', views.check_user_accounts, name='check_user_accounts'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Contas
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<uuid:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<uuid:account_id>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<uuid:account_id>/delete/', views.account_delete, name='account_delete'),
    path('accounts/<uuid:account_id>/toggle-status/', views.toggle_account_status, name='toggle_account_status'),
    
    # Membros das Contas
    path('accounts/<uuid:account_id>/members/', views.account_members, name='account_members'),
    path('accounts/<uuid:account_id>/members/add/', views.add_member, name='add_member'),
    path('accounts/<uuid:account_id>/members/<uuid:membership_id>/remove/', views.remove_member, name='remove_member'),
    path('accounts/<uuid:account_id>/members/<uuid:membership_id>/toggle-status/', views.toggle_member_status, name='toggle_member_status'),
    
    # Gerenciamento Global de Membros
    path('members/', views.all_members, name='all_members'),
    path('members/add/', views.add_member_to_account, name='add_member_to_account'),
    
    # Roles e Permissões
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:role_id>/', views.role_detail, name='role_detail'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    
    path('permissions/', views.permissions_list, name='permissions_list'),
    path('permissions/create/', views.permission_create, name='permission_create'),
    path('permissions/<int:permission_id>/', views.permission_detail, name='permission_detail'),
    path('permissions/<int:permission_id>/edit/', views.permission_edit, name='permission_edit'),
    path('permissions/<int:permission_id>/delete/', views.permission_delete, name='permission_delete'),
    
    # Analytics e Relatórios
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('export/users/', views.export_users, name='export_users'),
    path('export/accounts/', views.export_accounts, name='export_accounts'),
    
    # Sistema
    path('system/health/', views.system_health, name='system_health'),
    
    # Gerenciamento de Conteúdo
    path('content/', views.content_list, name='content_list'),
    path('content/<uuid:content_id>/', views.content_detail, name='content_detail'),
    path('content/<uuid:content_id>/toggle-status/', views.content_toggle_status, name='content_toggle_status'),
    path('content/<uuid:content_id>/delete/', views.content_delete, name='content_delete'),
    
    # Categorias
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/<uuid:category_id>/', views.category_detail, name='category_detail'),
    path('categories/<uuid:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # Tags
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/<uuid:tag_id>/', views.tag_detail, name='tag_detail'),
    path('tags/<uuid:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    
    # Domínios
    path('domains/', views.domains_list, name='domains_list'),
    path('domains/<uuid:domain_id>/', views.domain_detail, name='domain_detail'),
    path('domains/<uuid:domain_id>/verify/', views.domain_verify, name='domain_verify'),
    path('domains/<uuid:domain_id>/delete/', views.domain_delete, name='domain_delete'),
    
    # Configurações do Sistema
    path('settings/general/', views.admin_settings_general, name='admin_settings_general'),
    path('settings/security/', views.admin_settings_security, name='admin_settings_security'),
    path('settings/notifications/', views.admin_settings_notifications, name='admin_settings_notifications'),
    path('settings/appearance/', views.admin_settings_appearance, name='admin_settings_appearance'),
    
    # Gerenciamento de Sites
    path('sites/', include('site_management.urls')),
]