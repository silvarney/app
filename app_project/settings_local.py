"""
Arquivo de configurações locais temporárias para desenvolvimento
Este arquivo pode ser importado em settings.py para sobrescrever configurações padrão
"""

# Configuração temporária para SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# Configurar um ambiente para iniciar o servidor
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Django sites
    'django.contrib.sites',
    
    # Third party essenciais
    'rest_framework',
    'corsheaders',
    
    # Local apps 
    'users',
    'accounts',
    'permissions',
    'domains',
    'payments',
    'content',
    'uploads',
    'api',
    'admin_panel',
    'user_panel',
    'settings',
    'site_management',
]

# Configuração simplificada de middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configurações simplificadas para testes
SITE_ID = 1

# Usar URLs simplificadas para demonstração
ROOT_URLCONF = 'app_project.urls_local'
