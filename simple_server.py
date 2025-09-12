"""
Servidor web simples para demonstrar sucesso na migração para UUIDs
"""

import http.server
import socketserver

PAGE_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migração para UUID - Sucesso</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
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
        .uuid-info {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        h1 {
            color: #2196F3;
        }
        h2 {
            color: #333;
        }
        .uuid-example {
            font-family: monospace;
            background-color: #eee;
            padding: 3px 6px;
            border-radius: 3px;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Migração para UUID</h1>
        
        <div class="success-message">
            <h2>Migração concluída com sucesso!</h2>
            <p>Todos os modelos do sistema agora usam UUIDs como chaves primárias.</p>
        </div>
        
        <div class="uuid-info">
            <h2>Sobre UUIDs</h2>
            <p>UUIDs (Universally Unique Identifiers) são identificadores de 128 bits que garantem unicidade global, como por exemplo <span class="uuid-example">550e8400-e29b-41d4-a716-446655440000</span>.</p>
            
            <h3>Vantagens da migração:</h3>
            <ul>
                <li><strong>Segurança:</strong> UUIDs não revelam informações sobre o volume de dados no sistema.</li>
                <li><strong>Distribuição:</strong> Permitem a geração de IDs em diferentes servidores sem coordenação central.</li>
                <li><strong>Sincronização:</strong> Reduzem conflitos em sincronizações entre bancos de dados.</li>
                <li><strong>Integração:</strong> Facilitam a integração com sistemas externos e microserviços.</li>
                <li><strong>Privacidade:</strong> Não são sequenciais ou previsíveis como IDs incrementais.</li>
            </ul>
        </div>
        
        <div class="uuid-info">
            <h2>Modelos migrados</h2>
            <p>Os seguintes modelos foram migrados para usar UUIDs:</p>
            <ul>
                <li>User</li>
                <li>Account</li>
                <li>Site</li>
                <li>AccountMembership</li>
                <li>Permission</li>
                <li>Role</li>
                <li>Domain</li>
                <li>Payment</li>
                <li>Content</li>
                <li>... e todos os demais modelos do sistema</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

class UUIDHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(PAGE_HTML.encode())

def run_server():
    port = 8000
    handler = UUIDHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Servidor iniciado em http://localhost:{port}")
        print("Para encerrar o servidor, pressione Ctrl+C")
        print("Aguardando conexões...")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
