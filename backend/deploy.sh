#!/bin/bash

# Script de deploy para produção
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando deploy de produção..."

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Erro: execute este script do diretório backend/"
    exit 1
fi

# Verificar variáveis de ambiente obrigatórias
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "❌ Erro: DJANGO_SECRET_KEY não definida"
    exit 1
fi

if [ -z "$ALLOWED_HOSTS" ]; then
    echo "❌ Erro: ALLOWED_HOSTS não definido"
    exit 1
fi

if [ -z "$CORS_ALLOWED_ORIGINS" ]; then
    echo "❌ Erro: CORS_ALLOWED_ORIGINS não definido"
    exit 1
fi

# Ativar ambiente virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado. Criando..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Instalar/atualizar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Executar migrações
echo "🗄️  Executando migrações..."
export DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Verificar configurações
echo "✅ Verificando configurações..."
python manage.py check --deploy

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "Para iniciar o servidor com Gunicorn:"
echo "  gunicorn payevo_proxy.wsgi:application --bind 0.0.0.0:8000 --workers 4"
echo ""

