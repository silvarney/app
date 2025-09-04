from django.urls import path
from . import views

app_name = 'site_management'

urlpatterns = [
    # Sites CRUD
    path('', views.sites_list, name='sites_list'),
    path('create/', views.site_create, name='site_create'),
    path('<uuid:site_id>/', views.site_detail, name='site_detail'),
    path('<uuid:site_id>/edit/', views.site_edit, name='site_edit'),
    path('<uuid:site_id>/toggle-status/', views.site_toggle_status, name='site_toggle_status'),
    path('<uuid:site_id>/delete/', views.site_delete, name='site_delete'),
    
    # Bio do Site
    path('<uuid:site_id>/bio/edit/', views.site_bio_edit, name='site_bio_edit'),
]