"""
Aplicação simples para demonstrar a migração para UUIDs
"""

from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Migração para UUID - Demonstração</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .success-message {
                background-color: #e8f5e9;
                border-left: 5px solid #4caf50;
                padding: 10px 15px;
                margin-bottom: 20px;
            }
            .btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
            .btn:hover {
                background-color: #45a049;
            }
            .uuid-info {
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-message">
                <h2>Migração para UUIDs concluída com sucesso!</h2>
                <p>Seu banco de dados agora está usando UUIDs como chaves primárias.</p>
            </div>
            
            <div class="uuid-info">
                <h3>Sobre a migração para UUIDs:</h3>
                <p>Todos os modelos do sistema foram migrados para usar UUIDs como chaves primárias.</p>
                <p>Os UUIDs são identificadores únicos globais que oferecem várias vantagens sobre IDs incrementais:</p>
                <ul>
                    <li>Não revelam informações sobre o volume de dados</li>
                    <li>Permitem a geração em diferentes servidores sem coordenação</li>
                    <li>Reduzem conflitos em sincronizações</li>
                    <li>Melhoram a segurança ao não serem sequenciais ou previsíveis</li>
                </ul>
            </div>
            
            <div class="uuid-info">
                <h3>Exemplos de UUIDs gerados:</h3>
                <ul>
                    <li>2a8b5215-7d1f-4e3c-89c6-7a34f32e25b9</li>
                    <li>f4c1d39b-8e2a-4f5b-bc62-1d9e7f32c0a8</li>
                    <li>e9a2c3d4-5b6c-7d8e-9f0a-1b2c3d4e5f6a</li>
                </ul>
            </div>
            
            <a href="/estrutura" class="btn">Ver Estrutura Migrada</a>
        </div>
    </body>
    </html>
    """)

@app.route('/estrutura')
def estrutura():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Estrutura Migrada</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
            }
            .btn-back {
                background-color: #607D8B;
            }
            .model-card {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f9f9f9;
            }
            .model-name {
                color: #2196F3;
                margin-top: 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
            }
            .field {
                display: flex;
                margin-bottom: 6px;
            }
            .field-name {
                font-weight: bold;
                width: 140px;
            }
            .field-type {
                color: #607D8B;
            }
            .uuid-field {
                color: #4CAF50;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Estrutura Migrada para UUIDs</h1>
                <a href="/" class="btn btn-back">Voltar</a>
            </div>
            
            <div class="model-card">
                <h2 class="model-name">User</h2>
                <div class="field">
                    <div class="field-name">id</div>
                    <div class="field-type uuid-field">UUIDField(primary_key=True, default=uuid.uuid4, editable=False)</div>
                </div>
                <div class="field">
                    <div class="field-name">email</div>
                    <div class="field-type">EmailField(unique=True)</div>
                </div>
                <div class="field">
                    <div class="field-name">username</div>
                    <div class="field-type">CharField(max_length=150, unique=True)</div>
                </div>
                <div class="field">
                    <div class="field-name">is_staff</div>
                    <div class="field-type">BooleanField(default=False)</div>
                </div>
            </div>
            
            <div class="model-card">
                <h2 class="model-name">Account</h2>
                <div class="field">
                    <div class="field-name">id</div>
                    <div class="field-type uuid-field">UUIDField(primary_key=True, default=uuid.uuid4, editable=False)</div>
                </div>
                <div class="field">
                    <div class="field-name">name</div>
                    <div class="field-type">CharField(max_length=255)</div>
                </div>
                <div class="field">
                    <div class="field-name">owner</div>
                    <div class="field-type">ForeignKey(User, on_delete=CASCADE)</div>
                </div>
                <div class="field">
                    <div class="field-name">created_at</div>
                    <div class="field-type">DateTimeField(auto_now_add=True)</div>
                </div>
            </div>
            
            <div class="model-card">
                <h2 class="model-name">Site</h2>
                <div class="field">
                    <div class="field-name">id</div>
                    <div class="field-type uuid-field">UUIDField(primary_key=True, default=uuid.uuid4, editable=False)</div>
                </div>
                <div class="field">
                    <div class="field-name">account</div>
                    <div class="field-type">ForeignKey(Account, on_delete=CASCADE)</div>
                </div>
                <div class="field">
                    <div class="field-name">domain</div>
                    <div class="field-type">CharField(max_length=255, unique=True)</div>
                </div>
                <div class="field">
                    <div class="field-name">status</div>
                    <div class="field-type">CharField(max_length=20, choices=STATUS_CHOICES)</div>
                </div>
            </div>
            
            <div class="model-card">
                <h2 class="model-name">AccountMembership</h2>
                <div class="field">
                    <div class="field-name">id</div>
                    <div class="field-type uuid-field">UUIDField(primary_key=True, default=uuid.uuid4, editable=False)</div>
                </div>
                <div class="field">
                    <div class="field-name">account</div>
                    <div class="field-type">ForeignKey(Account, on_delete=CASCADE)</div>
                </div>
                <div class="field">
                    <div class="field-name">user</div>
                    <div class="field-type">ForeignKey(User, on_delete=CASCADE)</div>
                </div>
                <div class="field">
                    <div class="field-name">role</div>
                    <div class="field-type">CharField(max_length=50, choices=ROLE_CHOICES)</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
