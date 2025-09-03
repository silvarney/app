import requests
from bs4 import BeautifulSoup

# Fazer uma requisição simples para o formulário
url = 'http://127.0.0.1:8000/admin/users/create/'

print("=== TESTE SIMPLES DO FORMULÁRIO ===")
print(f"Acessando: {url}\n")

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Salvar HTML
        with open('form_current.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✅ HTML salvo em 'form_current.html'")
        
        # Analisar HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procurar por select user_type
        user_type_select = soup.find('select', {'name': 'user_type'})
        if user_type_select:
            print("\n✅ ENCONTRADO: <select name='user_type'>")
            options = user_type_select.find_all('option')
            print(f"Opções ({len(options)}):")
            for opt in options:
                value = opt.get('value', '')
                text = opt.get_text().strip()
                selected = 'selected' in opt.attrs
                print(f"  - '{value}' = '{text}' {'[SELECTED]' if selected else ''}")
        else:
            print("\n❌ NÃO ENCONTRADO: <select name='user_type'>")
            
        # Procurar por radio buttons
        radio_buttons = soup.find_all('input', {'name': 'user_type', 'type': 'radio'})
        if radio_buttons:
            print(f"\n⚠️  AINDA EXISTEM {len(radio_buttons)} radio buttons")
        else:
            print("\n✅ Nenhum radio button encontrado")
            
    else:
        print(f"❌ Erro: {response.status_code}")
        
except Exception as e:
    print(f"❌ Erro na requisição: {e}")

print("\n=== FIM DO TESTE ===")