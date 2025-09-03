from django.urls import path
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
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Contas
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/<uuid:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<uuid:account_id>/delete/', views.account_delete, name='account_delete'),
    path('accounts/<uuid:account_id>/toggle-status/', views.toggle_account_status, name='toggle_account_status'),
    
    # Roles e Permissões
    path('roles/', views.roles_list, name='roles_list'),
    path('permissions/', views.permissions_list, name='permissions_list'),
]