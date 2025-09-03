import requests
import re
from bs4 import BeautifulSoup

# Criar uma sessão para manter cookies
session = requests.Session()

# Primeiro, fazer login
login_url = 'http://127.0.0.1:8000/accounts/login/'
login_response = session.get(login_url)
login_soup = BeautifulSoup(login_response.content, 'html.parser')
login_csrf_token = login_soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

# Dados de login (usando superuser)
login_data = {
    'csrfmiddlewaretoken': login_csrf_token,
    'login': 'admin@admin.com',  # Email do superusuário criado
    'password': 'admin123',      # Senha do superusuário criado
    'next': '/admin/users/create/'
}

# Fazer login
login_post = session.post(login_url, data=login_data)
print(f"Login Status: {login_post.status_code}")
print(f"Login Final URL: {login_post.url}")
print(f"Login Response Headers: {dict(login_post.headers)}")

# Verificar se o login foi bem-sucedido
if 'login' in login_post.url:
    print("❌ ERRO: Login falhou - ainda na página de login")
    # Salvar resposta do login para debug
    with open('login_response.html', 'w', encoding='utf-8') as f:
        f.write(login_post.text)
    exit(1)
else:
    print("✅ Login bem-sucedido")

# URL do formulário
url = 'http://127.0.0.1:8000/admin/users/create/'

# Fazer GET para obter o formulário
get_response = session.get(url)
print(f"GET Status: {get_response.status_code}")
print(f"GET URL Final: {get_response.url}")

# Verificar se estamos na página correta
if 'login' in get_response.url:
    print("❌ ERRO: Ainda estamos na página de login!")
    print("Verificando se o login foi realmente bem-sucedido...")
    exit(1)

# Salvar HTML inicial do formulário
with open('form_initial.html', 'w', encoding='utf-8') as f:
    f.write(get_response.text)

# Extrair token CSRF
soup = BeautifulSoup(get_response.text, 'html.parser')
csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
if not csrf_input:
    print("❌ ERRO: Token CSRF não encontrado!")
    exit(1)
    
csrf_token = csrf_input['value']
print(f"CSRF Token: {csrf_token}")

# Verificar se encontramos o campo user_type
user_type_field = soup.find('input', {'name': 'user_type'})
if user_type_field:
    print("✅ Campo user_type encontrado no formulário")
else:
    print("❌ Campo user_type NÃO encontrado no formulário")

# Dados do formulário SEM user_type para replicar o erro
form_data = {
    'csrfmiddlewaretoken': csrf_token,
    'username': 'teste_erro_user_type',
    'email': 'teste_erro@example.com',
    'phone': '11999999999',
    'is_active': 'on',
    'status': 'active',
    'name': 'Usuario Teste Erro',
    'password': 'senha123',
    'confirm_password': 'senha123'
    # user_type propositalmente omitido para replicar o erro
}

print("\n=== Enviando formulário SEM user_type ===")
print(f"Dados enviados: {form_data}")

# Enviar o formulário
response = session.post(url, data=form_data)
print(f"\nPOST Status: {response.status_code}")

# Verificar se há erros na resposta
soup = BeautifulSoup(response.content, 'html.parser')

# Procurar por todos os erros de validação
all_errors = soup.find_all('div', {'class': re.compile(r'text-red-')})
if all_errors:
    print("\n=== ERROS DE VALIDAÇÃO ENCONTRADOS ===")
    for i, error in enumerate(all_errors, 1):
        print(f"{i}. {error.get_text().strip()}")

# Procurar especificamente por erros do user_type
user_type_section = soup.find('label', string=re.compile(r'Tipo de Usuário|User Type'))
if user_type_section:
    user_type_container = user_type_section.find_parent('div')
    if user_type_container:
        user_type_errors = user_type_container.find_all('div', {'class': re.compile(r'text-red-')})
        if user_type_errors:
            print("\n=== ERROS ESPECÍFICOS DO USER_TYPE ===")
            for error in user_type_errors:
                print(f"- {error.get_text().strip()}")

# Verificar se há mensagens de erro não relacionadas a campos específicos
non_field_error_containers = soup.find_all('div', {'class': re.compile(r'bg-red-')})
if non_field_error_containers:
    print("\n=== ERROS GERAIS (NÃO RELACIONADOS A CAMPOS) ===")
    for container in non_field_error_containers:
        error_text = container.get_text().strip()
        if error_text:
            print(f"- {error_text}")

# Verificar se o formulário ainda está sendo exibido (indicando erro)
form_element = soup.find('form')
if form_element:
    print("\n✓ ERRO REPLICADO: Formulário ainda está sendo exibido, indicando que houve erro de validação")
else:
    print("\n✗ Erro não replicado: Formulário foi processado com sucesso")

# Salvar o HTML da resposta para análise detalhada
with open('form_response.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("\nHTML da resposta salvo em 'form_response.html' para análise detalhada")

print("\n=== Teste de replicação de erro concluído ===")