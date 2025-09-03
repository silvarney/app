import requests
from bs4 import BeautifulSoup
import re

# Configurar sessão
session = requests.Session()

# URLs
login_url = 'http://127.0.0.1:8000/accounts/login/'
form_url = 'http://127.0.0.1:8000/admin/users/create/'

print("=== Teste de Formulário COM user_type selecionado ===")

# Fazer login
login_response = session.get(login_url)
login_soup = BeautifulSoup(login_response.text, 'html.parser')
login_csrf_token = login_soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

login_data = {
    'csrfmiddlewaretoken': login_csrf_token,
    'login': 'admin@admin.com',
    'password': 'admin123',
    'next': '/admin/users/create/'
}

login_post_response = session.post(login_url, data=login_data)
print(f"Login Status: {login_post_response.status_code}")

if 'login' in login_post_response.url:
    print("❌ ERRO: Login falhou")
    exit(1)
else:
    print("✅ Login bem-sucedido")

# Acessar formulário
get_response = session.get(form_url)
print(f"GET Status: {get_response.status_code}")

if 'login' in get_response.url:
    print("❌ ERRO: Redirecionado para login")
    exit(1)

# Extrair token CSRF
soup = BeautifulSoup(get_response.text, 'html.parser')
csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
if not csrf_input:
    print("❌ ERRO: Token CSRF não encontrado!")
    exit(1)
    
csrf_token = csrf_input['value']
print(f"CSRF Token: {csrf_token}")

# Dados do formulário COM user_type selecionado
form_data = {
    'csrfmiddlewaretoken': csrf_token,
    'username': 'teste_sucesso_user_type',
    'email': 'teste_sucesso@example.com',
    'phone': '11888888888',
    'is_active': 'on',
    'status': 'active',
    'user_type': 'user',  # INCLUINDO o user_type
    'name': 'Usuario Teste Sucesso',
    'password': 'senha123',
    'confirm_password': 'senha123'
}

print("\n=== Enviando formulário COM user_type selecionado ===")
print(f"Dados enviados: {form_data}")

# Enviar formulário
post_response = session.post(form_url, data=form_data)
print(f"\nPOST Status: {post_response.status_code}")
print(f"POST URL Final: {post_response.url}")

# Verificar se foi redirecionado (sucesso) ou se ainda está no formulário (erro)
if 'create' in post_response.url:
    print("❌ ERRO: Ainda no formulário, houve erro de validação")
    
    # Procurar por erros
    soup = BeautifulSoup(post_response.text, 'html.parser')
    
    # Procurar erros gerais
    error_divs = soup.find_all('div', {'class': re.compile(r'text-red-')})
    if error_divs:
        print("\n=== ERROS ENCONTRADOS ===")
        for i, error_div in enumerate(error_divs, 1):
            error_text = error_div.get_text(strip=True)
            if error_text:
                print(f"{i}. {error_text}")
    else:
        print("\n❓ Nenhum erro visível encontrado")
else:
    print("✅ SUCESSO: Usuário criado com sucesso! Redirecionado para:", post_response.url)

print("\n=== Teste concluído ===")