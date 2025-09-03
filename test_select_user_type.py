import requests
from bs4 import BeautifulSoup
import re
import time

# Configurar sessão
session = requests.Session()

# URLs
login_url = 'http://127.0.0.1:8000/accounts/login/'
form_url = 'http://127.0.0.1:8000/admin/users/create/'

print("=== TESTE DO SELECT USER_TYPE ===")
print("Verificando se o campo user_type é um select com 'Usuário Comum' como padrão...\n")

# 1. Fazer login
print("1. Fazendo login...")
login_response = session.get(login_url)
login_soup = BeautifulSoup(login_response.text, 'html.parser')
csrf_token = login_soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

login_data = {
    'csrfmiddlewaretoken': csrf_token,
    'username': 'admin',
    'password': 'admin123'
}

login_post = session.post(login_url, data=login_data)
if login_post.status_code == 200 and 'admin' in login_post.url:
    print("✅ Login bem-sucedido")
else:
    print("❌ Falha no login")
    exit(1)

# 2. Acessar formulário de criação
print("\n2. Acessando formulário de criação...")
form_response = session.get(form_url)

if form_response.status_code == 200:
    print("✅ Formulário acessado com sucesso")
    
    # Salvar HTML para análise
    with open('form_select_test.html', 'w', encoding='utf-8') as f:
        f.write(form_response.text)
    
    # Analisar o HTML
    soup = BeautifulSoup(form_response.text, 'html.parser')
    
    # Verificar se existe um select com name="user_type"
    user_type_select = soup.find('select', {'name': 'user_type'})
    
    if user_type_select:
        print("✅ Campo user_type é um SELECT")
        
        # Verificar as opções
        options = user_type_select.find_all('option')
        print(f"\nOpções encontradas ({len(options)}):")
        
        for i, option in enumerate(options):
            value = option.get('value', '')
            text = option.get_text().strip()
            selected = 'selected' in option.attrs
            status = "[SELECIONADO]" if selected else ""
            print(f"  {i+1}. value='{value}' text='{text}' {status}")
        
        # Verificar se 'user' está selecionado por padrão
        user_option = user_type_select.find('option', {'value': 'user'})
        if user_option and 'selected' in user_option.attrs:
            print("\n✅ 'Usuário Comum' está selecionado por padrão")
        else:
            print("\n❌ 'Usuário Comum' NÃO está selecionado por padrão")
            
    else:
        print("❌ Campo user_type NÃO é um select")
        # Verificar se ainda são radio buttons
        radio_buttons = soup.find_all('input', {'name': 'user_type', 'type': 'radio'})
        if radio_buttons:
            print(f"⚠️  Ainda existem {len(radio_buttons)} radio buttons")
else:
    print(f"❌ Erro ao acessar formulário: {form_response.status_code}")

print("\n=== FIM DO TESTE ===")