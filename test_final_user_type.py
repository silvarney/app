import requests
from bs4 import BeautifulSoup

# Configurar sessão
session = requests.Session()

print("=== TESTE FINAL DO CAMPO USER_TYPE ===")
print("1. Fazendo login...")

# Fazer login
login_url = 'http://127.0.0.1:8000/auth/login/'
login_response = session.get(login_url)

if login_response.status_code == 200:
    soup = BeautifulSoup(login_response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'email': 'admin@test.com',
        'password': 'admin123',
    }
    
    post_response = session.post(login_url, data=login_data)
    
    if 'admin' in post_response.url or post_response.status_code == 302:
        print("✅ Login realizado com sucesso")
        
        print("\n2. Acessando formulário de criação de usuário...")
        form_url = 'http://127.0.0.1:8000/admin/users/create/'
        form_response = session.get(form_url)
        
        if form_response.status_code == 200:
            print("✅ Formulário acessado com sucesso")
            
            # Salvar HTML
            with open('form_authenticated.html', 'w', encoding='utf-8') as f:
                f.write(form_response.text)
            print("✅ HTML salvo em 'form_authenticated.html'")
            
            # Analisar HTML
            soup = BeautifulSoup(form_response.text, 'html.parser')
            
            print("\n3. Verificando campo user_type...")
            
            # Procurar por select user_type
            user_type_select = soup.find('select', {'name': 'user_type'})
            if user_type_select:
                print("✅ ENCONTRADO: <select name='user_type'>")
                options = user_type_select.find_all('option')
                print(f"Opções ({len(options)}):")
                for opt in options:
                    value = opt.get('value', '')
                    text = opt.get_text().strip()
                    selected = 'selected' in opt.attrs
                    print(f"  - '{value}' = '{text}' {'[SELECTED]' if selected else ''}")
                    
                # Verificar se 'user' está selecionado por padrão
                user_option = user_type_select.find('option', {'value': 'user', 'selected': True})
                if user_option:
                    print("\n✅ 'Usuário Comum' está selecionado por padrão")
                else:
                    print("\n⚠️  'Usuário Comum' NÃO está selecionado por padrão")
                    
            else:
                print("❌ NÃO ENCONTRADO: <select name='user_type'>")
                
                # Procurar por qualquer campo user_type
                user_type_fields = soup.find_all(attrs={'name': 'user_type'})
                if user_type_fields:
                    print(f"\n⚠️  Encontrados {len(user_type_fields)} campos user_type de outros tipos:")
                    for field in user_type_fields:
                        print(f"  - {field.name} type='{field.get('type', 'N/A')}'")
                else:
                    print("\n❌ Nenhum campo user_type encontrado")
                    
        else:
            print(f"❌ Erro ao acessar formulário: {form_response.status_code}")
            
    else:
        print(f"❌ Falha no login: {post_response.status_code}")
        
else:
    print(f"❌ Erro ao acessar página de login: {login_response.status_code}")

print("\n=== FIM DO TESTE ===")