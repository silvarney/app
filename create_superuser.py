import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Verificar se já existe um superusuário
if User.objects.filter(is_superuser=True).exists():
    print("Superusuário já existe!")
    superuser = User.objects.filter(is_superuser=True).first()
    print(f"Email: {superuser.email}")
    print(f"Username: {superuser.username}")
else:
    # Criar superusuário
    superuser = User.objects.create_superuser(
        email='admin@admin.com',
        username='admin',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    
    # Confirmar o email do usuário
    from allauth.account.models import EmailAddress
    email_address, created = EmailAddress.objects.get_or_create(
        user=superuser,
        email=superuser.email,
        defaults={'verified': True, 'primary': True}
    )
    if not email_address.verified:
        email_address.verified = True
        email_address.save()
    
    print("Superusuário criado com sucesso!")
    print(f"Email: {superuser.email} (confirmado)")
    print(f"Username: {superuser.username}")
    print("Senha: admin123")