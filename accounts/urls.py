from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Gerenciamento de contas
    path('', views.account_list, name='list'),
    path('create/', views.account_create, name='create'),
    path('<uuid:account_id>/', views.account_detail, name='detail'),
    path('<uuid:account_id>/edit/', views.account_edit, name='edit'),
    path('<uuid:account_id>/delete/', views.account_delete, name='delete'),
    
    # Gerenciamento de membros
    path('<uuid:account_id>/invite/', views.member_invite, name='invite_member'),
    path('<uuid:account_id>/members/<uuid:membership_id>/edit/', views.member_edit, name='edit_member'),
    path('<uuid:account_id>/members/<uuid:membership_id>/remove/', views.member_remove, name='remove_member'),
    path('<uuid:account_id>/leave/', views.member_leave, name='leave_account'),
    
    # Gerenciamento de convites
    path('invitations/<str:token>/accept/', views.invitation_accept, name='accept_invitation'),
    path('invitations/<str:token>/decline/', views.invitation_decline, name='decline_invitation'),
    path('<uuid:account_id>/invitations/<uuid:invitation_id>/cancel/', views.invitation_cancel, name='cancel_invitation'),
]