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
    
    # Gerenciamento de Conteúdo
    path('content/', views.content_list, name='content_list'),
    path('content/create/', views.content_create, name='content_create'),
    path('content/<uuid:content_id>/', views.content_detail, name='content_detail'),
    path('content/<uuid:content_id>/edit/', views.content_edit, name='content_edit'),
    path('content/<uuid:content_id>/delete/', views.content_delete, name='content_delete'),
    path('content/<uuid:content_id>/toggle-status/', views.content_toggle_status, name='content_toggle_status'),
    
    # Gerenciamento de Sites
    path('sites/', include('site_management.urls')),
]