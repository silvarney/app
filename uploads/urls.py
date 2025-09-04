from django.urls import path
from . import views

app_name = 'uploads'

urlpatterns = [
    # Lista e upload de arquivos
    path('', views.file_list, name='file_list'),
    path('upload/', views.file_upload, name='file_upload'),
    
    # Gerenciamento de arquivos
    path('file/<uuid:file_id>/', views.file_detail, name='file_detail'),
    path('file/<uuid:file_id>/edit/', views.file_edit, name='file_edit'),
    path('file/<uuid:file_id>/delete/', views.file_delete, name='file_delete'),
    
    # Servir arquivos
    path('file/<uuid:file_id>/serve/', views.file_serve, name='file_serve'),
    path('thumbnail/<uuid:file_id>/<str:size>/', views.thumbnail_serve, name='thumbnail_serve'),
    
    # API endpoints
    path('quota-status/', views.quota_status, name='quota_status'),
    path('ajax-upload/', views.ajax_upload, name='ajax_upload'),
]