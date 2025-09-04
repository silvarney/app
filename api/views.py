from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string

from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

import json
import stripe
import logging
from datetime import datetime, timedelta

# Import permission utilities
from permissions.decorators import user_has_permission, user_has_role
from permissions.mixins import PermissionRequiredMixin
from .permissions import (
    IsAuthenticatedAndAccountMember, ContentPermission, DomainPermission
)

# Import models
from accounts.models import Account, AccountMembership
from users.models import User
from permissions.models import Permission, Role, UserRole, UserPermission
from payments.models import Plan, Subscription, Payment, Invoice
from content.models import Category, Tag, Content, ContentAttachment
from domains.models import Domain, DomainConfiguration, DomainVerificationLog

# Import serializers (we'll create these)
from .serializers import (
    AccountSerializer, UserSerializer, PermissionSerializer, RoleSerializer,
    PlanSerializer, SubscriptionSerializer, PaymentSerializer,
    LoginSerializer, RegisterSerializer, ProfileSerializer,
    PasswordResetSerializer, PasswordChangeSerializer,
    # Content Management Serializers
    CategorySerializer, TagSerializer, ContentSerializer, ContentAttachmentSerializer,
    # Domain Management Serializers
    DomainSerializer, DomainConfigurationSerializer, DomainVerificationLogSerializer
)

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Authentication Views
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'message': 'Login realizado com sucesso'
                })
            else:
                return Response({
                    'error': 'Credenciais inválidas'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Logout realizado com sucesso'})
        except:
            return Response({'error': 'Erro ao fazer logout'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Usuário criado com sucesso'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Implementar lógica de reset de senha
                # Por exemplo, enviar email com token
                return Response({'message': 'Email de recuperação enviado'})
            except User.DoesNotExist:
                return Response({'message': 'Email de recuperação enviado'})  # Não revelar se email existe
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Implementar confirmação de reset de senha
        return Response({'message': 'Senha alterada com sucesso'})


class PasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'message': 'Senha alterada com sucesso'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ViewSets for CRUD operations
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Usuários só podem ver contas às quais têm acesso
        return Account.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        ).distinct()
    
    def perform_create(self, serializer):
        # Definir o owner como o usuário atual
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        account = self.get_object()
        members = AccountMembership.objects.filter(account=account, status='active')
        # Serializar membros
        return Response({'members': []})
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        account = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role')
        
        # Implementar lógica de convite
        return Response({'message': 'Convite enviado com sucesso'})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'first_name', 'date_joined']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        # Filtrar usuários baseado nas contas do usuário atual
        user_accounts = Account.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        )
        
        return User.objects.filter(
            memberships__account__in=user_accounts,
            memberships__status='active'
        ).distinct()


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.filter(is_active=True)
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'codename', 'category']
    filterset_fields = ['permission_type', 'category', 'resource']


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'codename']
    ordering_fields = ['name', 'priority']
    ordering = ['priority']
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        )
        
        return Role.objects.filter(
            Q(account__in=user_accounts) | Q(is_system=True),
            is_active=True
        ).distinct()


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]  # Planos podem ser visualizados por todos
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['price', 'name']
    ordering = ['price']


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        )
        
        return Subscription.objects.filter(account__in=user_accounts)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_accounts = Account.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        )
        
        return Payment.objects.filter(subscription__account__in=user_accounts)


# Account Management Views
class SwitchAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        account_id = request.data.get('account_id')
        
        try:
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            # Atualizar sessão ou contexto do usuário
            request.session['current_account_id'] = account.id
            
            return Response({
                'message': 'Conta alterada com sucesso',
                'account': AccountSerializer(account).data
            })
        except Account.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada ou sem acesso'
            }, status=status.HTTP_404_NOT_FOUND)


class InviteUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        account_id = request.data.get('account_id')
        email = request.data.get('email')
        role_id = request.data.get('role_id')
        
        try:
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            # Verificar se usuário já existe
            try:
                user = User.objects.get(email=email)
                # Adicionar à conta se não estiver
                account_membership, created = AccountMembership.objects.get_or_create(
                    account=account,
                    user=user,
                    defaults={'status': 'active'}
                )
                
                if not created and account_membership.status == 'active':
                    return Response({
                        'error': 'Usuário já é membro desta conta'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                account_membership.status = 'active'
                account_membership.save()
                
                message = 'Usuário adicionado à conta com sucesso'
            except User.DoesNotExist:
                # Enviar convite por email
                # Implementar lógica de convite
                message = 'Convite enviado por email'
            
            return Response({'message': message})
            
        except Account.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


class AccountMembersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        account_id = request.query_params.get('account_id')
        
        try:
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            members = AccountMembership.objects.filter(
                account=account,
                status='active'
            ).select_related('user')
            
            members_data = []
            for member in members:
                user_roles = UserRole.objects.filter(
                    user=member.user,
                    account=account,
                    status='active'
                ).select_related('role')
                
                members_data.append({
                    'user': UserSerializer(member.user).data,
                    'roles': [role.role.name for role in user_roles],
                    'joined_at': member.created_at
                })
            
            return Response({'members': members_data})
            
        except Account.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


# Permission Management Views
class CheckPermissionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        permission_codename = request.data.get('permission')
        account_id = request.data.get('account_id')
        
        # Implementar lógica de verificação de permissão
        # Verificar permissões diretas e por roles
        
        has_permission = False  # Placeholder
        
        return Response({
            'has_permission': has_permission,
            'permission': permission_codename
        })


class AssignRoleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        account_id = request.data.get('account_id')
        
        try:
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)
            
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                account=account,
                defaults={
                    'status': 'active',
                    'assigned_by': request.user
                }
            )
            
            if not created:
                user_role.status = 'active'
                user_role.assigned_by = request.user
                user_role.save()
            
            return Response({
                'message': 'Role atribuída com sucesso'
            })
            
        except (Account.DoesNotExist, User.DoesNotExist, Role.DoesNotExist) as e:
            return Response({
                'error': 'Recurso não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class RevokeRoleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        account_id = request.data.get('account_id')
        
        try:
            user_role = UserRole.objects.get(
                user_id=user_id,
                role_id=role_id,
                account_id=account_id
            )
            
            user_role.status = 'revoked'
            user_role.save()
            
            return Response({
                'message': 'Role revogada com sucesso'
            })
            
        except UserRole.DoesNotExist:
            return Response({
                'error': 'Role não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


# Billing & Payment Views
class CreateCheckoutSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        plan_id = request.data.get('plan_id')
        account_id = request.data.get('account_id')
        
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            # Criar sessão do Stripe Checkout
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': plan.name,
                            'description': plan.description,
                        },
                        'unit_amount': int(plan.price * 100),  # Stripe usa centavos
                        'recurring': {
                            'interval': plan.billing_cycle,
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri('/billing/success/'),
                cancel_url=request.build_absolute_uri('/billing/cancel/'),
                client_reference_id=f"{account.id}_{plan.id}",
                metadata={
                    'account_id': account.id,
                    'plan_id': plan.id,
                    'user_id': request.user.id
                }
            )
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            })
            
        except (Plan.DoesNotExist, Account.DoesNotExist):
            return Response({
                'error': 'Plano ou conta não encontrados'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erro ao criar sessão de checkout: {str(e)}")
            return Response({
                'error': 'Erro interno do servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
        
        # Processar eventos do Stripe
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session_completed(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            self.handle_payment_succeeded(invoice)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self.handle_subscription_cancelled(subscription)
        
        return HttpResponse(status=200)
    
    def handle_checkout_session_completed(self, session):
        # Implementar lógica de criação de assinatura
        pass
    
    def handle_payment_succeeded(self, invoice):
        # Implementar lógica de pagamento bem-sucedido
        pass
    
    def handle_subscription_cancelled(self, subscription):
        # Implementar lógica de cancelamento de assinatura
        pass


class CancelSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        subscription_id = request.data.get('subscription_id')
        
        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                account__memberships__user=request.user,
            account__memberships__status='active'
            )
            
            # Cancelar no Stripe
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # Atualizar status local
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()
            
            return Response({
                'message': 'Assinatura cancelada com sucesso'
            })
            
        except Subscription.DoesNotExist:
            return Response({
                'error': 'Assinatura não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


class UpdatePaymentMethodAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Implementar atualização de método de pagamento
        return Response({
            'message': 'Método de pagamento atualizado com sucesso'
        })


# Analytics Views
class DashboardAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        account_id = request.query_params.get('account_id')
        
        try:
            account = Account.objects.get(
                id=account_id,
                memberships__user=request.user,
            memberships__status='active'
            )
            
            # Calcular métricas do dashboard
            total_users = AccountMembership.objects.filter(
                account=account,
                status='active'
            ).count()
            
            active_subscription = Subscription.objects.filter(
                account=account,
                status='active'
            ).first()
            
            monthly_revenue = Payment.objects.filter(
                subscription__account=account,
                created_at__gte=timezone.now() - timedelta(days=30),
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            return Response({
                'total_users': total_users,
                'subscription': SubscriptionSerializer(active_subscription).data if active_subscription else None,
                'monthly_revenue': monthly_revenue,
                'account': AccountSerializer(account).data
            })
            
        except Account.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


class UsageAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Implementar analytics de uso
        return Response({
            'api_calls': 0,
            'storage_used': 0,
            'bandwidth_used': 0
        })


class ExportReportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        report_type = request.data.get('type')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        # Implementar exportação de relatórios
        return Response({
            'message': 'Relatório gerado com sucesso',
            'download_url': '/api/reports/download/123/'
        })


# API Keys Management
class APIKeyListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Listar chaves API do usuário
        return Response({'api_keys': []})
    
    def post(self, request):
        # Criar nova chave API
        return Response({
            'message': 'Chave API criada com sucesso',
            'api_key': 'sk_test_...',
            'name': request.data.get('name')
        })


class APIKeyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        # Deletar chave API
        return Response({
            'message': 'Chave API removida com sucesso'
        })


# Health Check
class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })


# Content Management ViewSets
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedAndAccountMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Category.objects.all()
        
        # Filtrar por contas do usuário
        user_accounts = user.memberships.values_list('account_id', flat=True)
        return Category.objects.filter(account_id__in=user_accounts)
    
    def perform_create(self, serializer):
        # Definir a conta baseada no usuário atual
        account = self.request.user.memberships.first().account
        serializer.save(account=account)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedAndAccountMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tag.objects.all()
        
        # Filtrar por contas do usuário
        user_accounts = user.memberships.values_list('account_id', flat=True)
        return Tag.objects.filter(account_id__in=user_accounts)
    
    def perform_create(self, serializer):
        # Definir a conta baseada no usuário atual
        account = self.request.user.memberships.first().account
        serializer.save(account=account)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'content_type', 'category', 'is_featured']
    search_fields = ['title', 'content', 'excerpt', 'meta_title', 'meta_description']
    ordering_fields = ['title', 'published_at', 'created_at', 'views_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Content.objects.all()
        
        if user.is_authenticated:
            # Filtrar por contas do usuário
            user_accounts = user.memberships.values_list('account_id', flat=True)
            return Content.objects.filter(account_id__in=user_accounts)
        else:
            # Para usuários não autenticados, mostrar apenas conteúdo público
            return Content.objects.filter(status='published')
    
    def perform_create(self, serializer):
        # Definir a conta e autor baseado no usuário atual
        account = self.request.user.memberships.first().account
        serializer.save(account=account, author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        content = self.get_object()
        content.status = 'published'
        content.published_at = timezone.now()
        content.save()
        return Response({'message': 'Conteúdo publicado com sucesso'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        content = self.get_object()
        content.status = 'draft'
        content.save()
        return Response({'message': 'Conteúdo despublicado com sucesso'})
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original_content = self.get_object()
        
        # Criar uma cópia do conteúdo
        new_content = Content.objects.create(
            title=f"{original_content.title} (Cópia)",
            content=original_content.content,
            excerpt=original_content.excerpt,
            content_type=original_content.content_type,
            category=original_content.category,
            account=original_content.account,
            author=request.user,
            status='draft'
        )
        
        # Copiar tags
        new_content.tags.set(original_content.tags.all())
        
        serializer = self.get_serializer(new_content)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ContentAttachment.objects.all()
    serializer_class = ContentAttachmentSerializer
    permission_classes = [IsAuthenticatedAndAccountMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['file_type']
    search_fields = ['file_name', 'alt_text', 'caption']
    ordering_fields = ['file_name', 'uploaded_at', 'order']
    ordering = ['order', 'uploaded_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ContentAttachment.objects.all()
        
        # Filtrar por contas do usuário através do conteúdo
        user_accounts = user.memberships.values_list('account_id', flat=True)
        return ContentAttachment.objects.filter(content__account_id__in=user_accounts)


# Domain Management ViewSets
class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [DomainPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'domain_type', 'is_active', 'is_primary', 'ssl_enabled']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'verified_at']
    ordering = ['-is_primary', 'name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Domain.objects.all()
        
        # Filtrar por contas do usuário
        user_accounts = user.memberships.values_list('account_id', flat=True)
        return Domain.objects.filter(account_id__in=user_accounts)
    
    def perform_create(self, serializer):
        # Definir a conta baseada no usuário atual
        account = self.request.user.memberships.first().account
        serializer.save(account=account)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        domain = self.get_object()
        
        if domain.verification_method == 'dns_txt':
            success = domain.verify_dns_txt()
        elif domain.verification_method == 'dns_cname':
            success = domain.verify_dns_cname()
        else:
            return Response(
                {'error': 'Método de verificação não suportado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if success:
            return Response({'message': 'Domínio verificado com sucesso'})
        else:
            return Response(
                {'error': 'Falha na verificação do domínio'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        domain = self.get_object()
        
        # Remover primary de outros domínios da mesma conta
        Domain.objects.filter(account=domain.account, is_primary=True).update(is_primary=False)
        
        # Definir este domínio como primary
        domain.is_primary = True
        domain.save()
        
        return Response({'message': 'Domínio definido como principal'})


class DomainConfigurationViewSet(viewsets.ModelViewSet):
    queryset = DomainConfiguration.objects.all()
    serializer_class = DomainConfigurationSerializer
    permission_classes = [IsAuthenticatedAndAccountMember]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return DomainConfiguration.objects.all()
        
        # Filtrar por contas do usuário através do domínio
        user_accounts = user.memberships.values_list('account_id', flat=True)
        return DomainConfiguration.objects.filter(domain__account_id__in=user_accounts)
