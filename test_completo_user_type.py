import requests
from bs4 import BeautifulSoup
import re
import time

# Configurar sessão
session = requests.Session()

# URLs
login_url = 'http://127.0.0.1:8000/accounts/login/'
form_url = 'http://127.0.0.1:8000/admin/users/create/'

print("=== TESTE COMPLETO DO FORMULÁRIO USER_TYPE ===")
print("Testando cenários de erro e sucesso...\n")

def fazer_login():
    """Faz login e retorna True se bem-sucedido"""
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
    return 'login' not in login_post_response.url

def obter_csrf_token():
    """Obtém o token CSRF do formulário"""
    get_response = session.get(form_url)
    soup = BeautifulSoup(get_response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    return csrf_input['value'] if csrf_input else None

def contar_erros_user_type(html_content):
    """Conta quantas vezes a mensagem de erro do user_type aparece"""
    soup = BeautifulSoup(html_content, 'html.parser')
    erro_msg = "Você deve selecionar um tipo de usuário."
    
    # Procurar em todos os elementos de texto
    all_text = soup.get_text()
    count = all_text.count(erro_msg)
    
    # Procurar especificamente em divs de erro
    error_divs = soup.find_all('div', {'class': re.compile(r'text-red-')})
    error_texts = [div.get_text(strip=True) for div in error_divs]
    
    return count, error_texts

# TESTE 1: Login
print("1. Fazendo login...")
if not fazer_login():
    print("❌ ERRO: Login falhou")
    exit(1)
print("✅ Login bem-sucedido")

# TESTE 2: Formulário SEM user_type (deve dar erro)
print("\n2. Testando formulário SEM user_type...")
csrf_token = obter_csrf_token()
if not csrf_token:
    print("❌ ERRO: Token CSRF não encontrado")
    exit(1)

form_data_erro = {
    'csrfmiddlewaretoken': csrf_token,
    'username': f'teste_erro_{int(time.time())}',
    'email': f'teste_erro_{int(time.time())}@example.com',
    'phone': '11999999999',
    'is_active': 'on',
    'status': 'active',
    'name': 'Usuario Teste Erro',
    'password': 'senha123',
    'confirm_password': 'senha123'
    # Propositalmente SEM user_type
}

post_response_erro = session.post(form_url, data=form_data_erro)
count_erros, error_texts = contar_erros_user_type(post_response_erro.text)

print(f"Status da resposta: {post_response_erro.status_code}")
print(f"URL final: {post_response_erro.url}")
print(f"Número de vezes que a mensagem de erro aparece: {count_erros}")
print(f"Textos de erro encontrados: {error_texts}")

if count_erros == 1:
    print("✅ SUCESSO: Apenas UMA mensagem de erro exibida (duplicação corrigida)")
elif count_erros > 1:
    print(f"❌ ERRO: {count_erros} mensagens duplicadas ainda existem!")
else:
    print("❌ ERRO: Nenhuma mensagem de erro encontrada (validação não funcionou)")

# TESTE 3: Formulário COM user_type (deve funcionar)
print("\n3. Testando formulário COM user_type...")
csrf_token = obter_csrf_token()  # Novo token

form_data_sucesso = {
    'csrfmiddlewaretoken': csrf_token,
    'username': f'teste_sucesso_{int(time.time())}',
    'email': f'teste_sucesso_{int(time.time())}@example.com',
    'phone': '11888888888',
    'is_active': 'on',
    'status': 'active',
    'user_type': 'user',  # COM user_type
    'name': 'Usuario Teste Sucesso',
    'password': 'senha123',
    'confirm_password': 'senha123'
}

post_response_sucesso = session.post(form_url, data=form_data_sucesso)

print(f"Status da resposta: {post_response_sucesso.status_code}")
print(f"URL final: {post_response_sucesso.url}")

if 'create' in post_response_sucesso.url:
    print("❌ ERRO: Ainda no formulário, criação falhou")
    # Verificar se há erros
    count_erros_sucesso, error_texts_sucesso = contar_erros_user_type(post_response_sucesso.text)
    if count_erros_sucesso > 0:
        print(f"Erros encontrados: {error_texts_sucesso}")
else:
    print("✅ SUCESSO: Usuário criado com sucesso! Redirecionado para lista")

print("\n=== RESUMO DOS TESTES ===")
print(f"Teste de erro (sem user_type): {'✅ PASSOU' if count_erros == 1 else '❌ FALHOU'}")
print(f"Teste de sucesso (com user_type): {'✅ PASSOU' if 'create' not in post_response_sucesso.url else '❌ FALHOU'}")

if count_erros == 1 and 'create' not in post_response_sucesso.url:
    print("\n🎉 TODOS OS TESTES PASSARAM! O problema foi resolvido.")
else:
    print("\n❌ ALGUNS TESTES FALHARAM! O problema ainda existe.")