from django.shortcuts import render
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import Account, AccountMembership
from api.permissions import IsAuthenticatedAndAccountMember
from .models import GlobalSetting, AccountSetting, UserSetting, SettingTemplate
from .serializers import (
    GlobalSettingSerializer, AccountSettingSerializer, UserSettingSerializer,
    SettingTemplateSerializer, SettingValueSerializer, BulkSettingsSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class GlobalSettingViewSet(viewsets.ModelViewSet):
    """ViewSet para configurações globais - apenas superusuários"""
    queryset = GlobalSetting.objects.all()
    serializer_class = GlobalSettingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'setting_type', 'is_public', 'is_editable']
    search_fields = ['key', 'description', 'category']
    ordering_fields = ['key', 'category', 'created_at']
    ordering = ['category', 'key']
    
    def get_permissions(self):
        """Apenas superusuários podem gerenciar configurações globais"""
        if self.action in ['list', 'retrieve'] and self.get_object().is_public:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filtra configurações baseado nas permissões do usuário"""
        if self.request.user.is_superuser:
            return GlobalSetting.objects.all()
        # Usuários normais só veem configurações públicas
        return GlobalSetting.objects.filter(is_public=True)
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """Retorna apenas configurações públicas"""
        settings = GlobalSetting.objects.filter(is_public=True)
        serializer = self.get_serializer(settings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_value(self, request, pk=None):
        """Atualiza apenas o valor de uma configuração"""
        setting = self.get_object()
        serializer = SettingValueSerializer(
            data=request.data,
            context={'setting': setting}
        )
        if serializer.is_valid():
            setting.value = serializer.validated_data['value']
            setting.save()
            return Response(GlobalSettingSerializer(setting).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountSettingViewSet(viewsets.ModelViewSet):
    """ViewSet para configurações de conta"""
    queryset = AccountSetting.objects.all()
    serializer_class = AccountSettingSerializer
    permission_classes = [IsAuthenticatedAndAccountMember]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'setting_type', 'is_inherited']
    search_fields = ['key', 'description', 'category']
    ordering_fields = ['key', 'category', 'created_at']
    ordering = ['category', 'key']
    
    def get_queryset(self):
        """Filtra configurações da conta atual do usuário"""
        if not hasattr(self.request.user, 'current_account'):
            return AccountSetting.objects.none()
        
        account = self.request.user.current_account
        return AccountSetting.objects.filter(account=account)
    
    def perform_create(self, serializer):
        """Associa a configuração à conta atual"""
        account = self.request.user.current_account
        serializer.save(account=account)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Retorna configurações agrupadas por categoria"""
        settings = self.get_queryset()
        categories = {}
        
        for setting in settings:
            category = setting.category or 'Geral'
            if category not in categories:
                categories[category] = []
            categories[category].append(AccountSettingSerializer(setting).data)
        
        return Response(categories)
    
    @action(detail=True, methods=['patch'])
    def update_value(self, request, pk=None):
        """Atualiza apenas o valor de uma configuração"""
        setting = self.get_object()
        serializer = SettingValueSerializer(
            data=request.data,
            context={'setting': setting}
        )
        if serializer.is_valid():
            setting.value = serializer.validated_data['value']
            setting.save()
            return Response(AccountSettingSerializer(setting).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Atualiza múltiplas configurações de uma vez"""
        serializer = BulkSettingsSerializer(data=request.data)
        if serializer.is_valid():
            account = self.request.user.current_account
            updated_settings = []
            
            for key, value in serializer.validated_data['settings'].items():
                setting, created = AccountSetting.objects.get_or_create(
                    account=account,
                    key=key,
                    defaults={'value': value, 'setting_type': 'string'}
                )
                if not created:
                    setting.value = value
                    setting.save()
                updated_settings.append(setting)
            
            return Response({
                'message': f'{len(updated_settings)} configurações atualizadas',
                'settings': AccountSettingSerializer(updated_settings, many=True).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSettingViewSet(viewsets.ModelViewSet):
    """ViewSet para configurações de usuário"""
    queryset = UserSetting.objects.all()
    serializer_class = UserSettingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'setting_type', 'is_inherited']
    search_fields = ['key', 'description', 'category']
    ordering_fields = ['key', 'category', 'created_at']
    ordering = ['category', 'key']
    
    def get_queryset(self):
        """Filtra configurações do usuário atual"""
        return UserSetting.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associa a configuração ao usuário atual"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Retorna configurações agrupadas por categoria"""
        settings = self.get_queryset()
        categories = {}
        
        for setting in settings:
            category = setting.category or 'Geral'
            if category not in categories:
                categories[category] = []
            categories[category].append(UserSettingSerializer(setting).data)
        
        return Response(categories)
    
    @action(detail=True, methods=['patch'])
    def update_value(self, request, pk=None):
        """Atualiza apenas o valor de uma configuração"""
        setting = self.get_object()
        serializer = SettingValueSerializer(
            data=request.data,
            context={'setting': setting}
        )
        if serializer.is_valid():
            setting.value = serializer.validated_data['value']
            setting.save()
            return Response(UserSettingSerializer(setting).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Atualiza múltiplas configurações de uma vez"""
        serializer = BulkSettingsSerializer(data=request.data)
        if serializer.is_valid():
            user = self.request.user
            updated_settings = []
            
            for key, value in serializer.validated_data['settings'].items():
                setting, created = UserSetting.objects.get_or_create(
                    user=user,
                    key=key,
                    defaults={'value': value, 'setting_type': 'string'}
                )
                if not created:
                    setting.value = value
                    setting.save()
                updated_settings.append(setting)
            
            return Response({
                'message': f'{len(updated_settings)} configurações atualizadas',
                'settings': UserSettingSerializer(updated_settings, many=True).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SettingTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para templates de configurações - apenas leitura"""
    queryset = SettingTemplate.objects.all()
    serializer_class = SettingTemplateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'setting_type', 'scope', 'is_required', 'is_public']
    search_fields = ['key', 'name', 'description', 'category']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['category', 'name']
    
    @action(detail=False, methods=['get'])
    def by_scope(self, request):
        """Retorna templates agrupados por escopo"""
        scope = request.query_params.get('scope')
        if scope:
            templates = self.queryset.filter(scope=scope)
        else:
            templates = self.queryset.all()
        
        scopes = {}
        for template in templates:
            if template.scope not in scopes:
                scopes[template.scope] = []
            scopes[template.scope].append(SettingTemplateSerializer(template).data)
        
        return Response(scopes)


class SettingsManagerAPIView(APIView):
    """API para gerenciar configurações de forma unificada"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retorna todas as configurações do usuário (globais públicas + conta + usuário)"""
        data = {
            'global': [],
            'account': [],
            'user': []
        }
        
        # Configurações globais públicas
        global_settings = GlobalSetting.objects.filter(is_public=True)
        data['global'] = GlobalSettingSerializer(global_settings, many=True).data
        
        # Configurações da conta (se o usuário tem conta atual)
        if hasattr(request.user, 'current_account'):
            account_settings = AccountSetting.objects.filter(
                account=request.user.current_account
            )
            data['account'] = AccountSettingSerializer(account_settings, many=True).data
        
        # Configurações do usuário
        user_settings = UserSetting.objects.filter(user=request.user)
        data['user'] = UserSettingSerializer(user_settings, many=True).data
        
        return Response(data)
    
    def post(self, request):
        """Cria configurações baseadas em templates"""
        template_keys = request.data.get('templates', [])
        scope = request.data.get('scope', 'user')
        
        if not template_keys:
            return Response(
                {'error': 'Lista de templates é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        templates = SettingTemplate.objects.filter(
            key__in=template_keys,
            scope=scope
        )
        
        created_settings = []
        
        for template in templates:
            if scope == 'global':
                if not request.user.is_superuser:
                    continue
                setting, created = GlobalSetting.objects.get_or_create(
                    key=template.key,
                    defaults={
                        'value': template.default_value,
                        'setting_type': template.setting_type,
                        'description': template.description,
                        'category': template.category,
                        'is_public': template.is_public
                    }
                )
            elif scope == 'account':
                if not hasattr(request.user, 'current_account'):
                    continue
                setting, created = AccountSetting.objects.get_or_create(
                    account=request.user.current_account,
                    key=template.key,
                    defaults={
                        'value': template.default_value,
                        'setting_type': template.setting_type,
                        'description': template.description,
                        'category': template.category
                    }
                )
            elif scope == 'user':
                setting, created = UserSetting.objects.get_or_create(
                    user=request.user,
                    key=template.key,
                    defaults={
                        'value': template.default_value,
                        'setting_type': template.setting_type,
                        'description': template.description,
                        'category': template.category
                    }
                )
            
            if created:
                created_settings.append(setting)
        
        return Response({
            'message': f'{len(created_settings)} configurações criadas',
            'created_count': len(created_settings)
        })


class SettingValueAPIView(APIView):
    """API para obter valor específico de uma configuração"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, scope, key):
        """Obtém o valor de uma configuração específica"""
        setting = None
        
        if scope == 'global':
            try:
                setting = GlobalSetting.objects.get(key=key, is_public=True)
            except GlobalSetting.DoesNotExist:
                pass
        elif scope == 'account':
            if hasattr(request.user, 'current_account'):
                try:
                    setting = AccountSetting.objects.get(
                        account=request.user.current_account,
                        key=key
                    )
                except AccountSetting.DoesNotExist:
                    pass
        elif scope == 'user':
            try:
                setting = UserSetting.objects.get(user=request.user, key=key)
            except UserSetting.DoesNotExist:
                pass
        
        if not setting:
            return Response(
                {'error': 'Configuração não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'key': setting.key,
            'value': setting.value,
            'typed_value': setting.get_typed_value(),
            'setting_type': setting.setting_type
        })
