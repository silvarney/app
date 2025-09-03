from django.urls import path
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
]