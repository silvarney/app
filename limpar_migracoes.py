"""
Script para remover arquivos de migração e limpar o banco de dados
"""
import os
import shutil

def limpar_migracoes():
    """Remove todos os arquivos de migração exceto __init__.py"""
    apps = ['accounts', 'admin_panel', 'api', 'content', 'domains', 'payments', 
           'permissions', 'settings', 'site_management', 'tasks', 'users', 'uploads']
    
    for app in apps:
        migration_dir = os.path.join(app, 'migrations')
        
        if os.path.exists(migration_dir):
            print(f"Processando diretório: {migration_dir}")
            
            # Manter apenas o __init__.py
            for filename in os.listdir(migration_dir):
                if filename != '__init__.py' and filename.endswith('.py'):
                    filepath = os.path.join(migration_dir, filename)
                    try:
                        os.remove(filepath)
                        print(f"Removido: {filepath}")
                    except Exception as e:
                        print(f"Erro ao remover {filepath}: {e}")
                
                # Remover arquivos .pyc em __pycache__ se existir
                pycache_dir = os.path.join(migration_dir, '__pycache__')
                if os.path.exists(pycache_dir):
                    try:
                        shutil.rmtree(pycache_dir)
                        print(f"Removido diretório: {pycache_dir}")
                    except Exception as e:
                        print(f"Erro ao remover {pycache_dir}: {e}")

if __name__ == "__main__":
    print("Iniciando limpeza de arquivos de migração...")
    limpar_migracoes()
    print("Limpeza concluída.")
