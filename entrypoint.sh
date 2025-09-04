#!/bin/bash
set -e

echo "Iniciando entrypoint.sh..."

# Função para aguardar serviço ficar disponível
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "Aguardando $service_name ($host:$port)..."
    while ! nc -z $host $port; do
        echo "$service_name não está pronto ainda. Aguardando..."
        sleep 2
    done
    echo "$service_name está pronto!"
}

# Aguarda PostgreSQL
wait_for_service "postgres" "5432" "PostgreSQL"

# Aguarda Redis
wait_for_service "redis" "6379" "Redis"

echo "Todos os serviços estão prontos. Iniciando aplicação..."

# Executa migrações do banco de dados
echo "Executando migrações..."
python manage.py migrate --noinput

# Coleta arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Inicialização concluída. Executando comando: $@"

# Executa o comando passado como argumento
exec "$@"