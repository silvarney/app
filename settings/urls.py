from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'global', views.GlobalSettingViewSet)
router.register(r'account', views.AccountSettingViewSet)
router.register(r'user', views.UserSettingViewSet)
router.register(r'templates', views.SettingTemplateViewSet)

app_name = 'settings'

urlpatterns = [
    # Incluir rotas do router
    path('', include(router.urls)),
    
    # APIs específicas
    path('manager/', views.SettingsManagerAPIView.as_view(), name='settings_manager'),
    path('value/<str:scope>/<str:key>/', views.SettingValueAPIView.as_view(), name='setting_value'),
]