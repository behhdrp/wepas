# Projeto Kore

Sistema de pagamentos com integração KorePay (PIX) - Frontend React + Backend Django

## 📋 Índice

- [Início Rápido](#-início-rápido)
- [Deploy para Produção](#-deploy-para-produção)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Endpoints da API](#-endpoints-da-api)
- [Configuração](#-configuração)

## 🚀 Início Rápido

### Opção 1: Script Automático (Recomendado)

```bash
./start.sh
```

### Opção 2: Manual

#### Backend (Django)

```bash
cd backend

# Criar ambiente virtual (se não existir)
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000
```

## 📁 Estrutura do Projeto

```
kore/
├── backend/          # API Django
│   ├── payments/     # App de pagamentos
│   └── payevo_proxy/ # Configurações Django
├── html/             # Frontend React (build)
└── start.sh          # Script de inicialização
```

## 🔌 Endpoints da API

### Criar Transação PIX
```
POST http://localhost:8000/api/transactions/pix/
Content-Type: application/json

{
  "amount": 10000,
  "customer": {
    "name": "João Silva",
    "email": "joao@example.com",
    "phone": "11999999999",
    "document": "12345678900"
  },
  "items": [
    {
      "title": "Produto",
      "unitPrice": 10000,
      "quantity": 1
    }
  ],
  "paymentMethod": "pix"
}
```

### Verificar Status da Transação
```
GET http://localhost:8000/api/transactions/status/?id={transaction_id}
```

### Webhook (Postback)
```
POST http://localhost:8000/api/postbacks/payevo/
```

## ⚙️ Configuração

### Variáveis de Ambiente

As seguintes variáveis podem ser configuradas:

- `DJANGO_SECRET_KEY`: Chave secreta do Django (padrão: "dev-secret")
- `PUBLIC_BASE_URL`: URL pública do servidor (padrão: "http://localhost:8000")
- `PAYEVO_SECRET_KEY`: Chave secreta do Payevo (opcional)
- `KOREPAY_SECRET_KEY`: Chave secreta do KorePay (já configurada)
- `KOREPAY_COMPANY_ID`: ID da empresa KorePay (já configurado)
- `UTMIFY_TOKEN`: Token do UTMify (já configurado)

### Gateway Padrão

O sistema está configurado para usar **KorePay** como gateway padrão. Para usar Payevo, adicione `?gate=payevo` na requisição.

## 🔧 Correções Implementadas

1. ✅ **Servir Frontend**: Django configurado para servir arquivos HTML estáticos
2. ✅ **CORS**: Configuração completa de CORS para permitir requisições do frontend
3. ✅ **Gateway KorePay**: Integração completa com KorePay como padrão
4. ✅ **URLs da API**: Endpoints corrigidos e funcionais
5. ✅ **Webhook**: Suporte para postbacks do KorePay e Payevo
6. ✅ **Tratamento de Erros**: Melhor tratamento de erros nas requisições

## 🚀 Deploy para Produção

**⚠️ IMPORTANTE**: O projeto está configurado para produção, mas requer configuração de variáveis de ambiente.

### Guias Disponíveis:

1. **LEIA-ME-PRODUCAO.md** - Resumo rápido e checklist
2. **DEPLOY.md** - Guia completo passo a passo
3. **PRODUCTION_CHECKLIST.md** - Checklist detalhado de segurança

### Início Rápido para Produção:

```bash
# 1. Configurar variáveis obrigatórias
export DJANGO_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
export ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
export CORS_ALLOWED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
export KOREPAY_SECRET_KEY=sua-chave
export KOREPAY_COMPANY_ID=seu-id

# 2. Usar settings de produção
export DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production

# 3. Deploy
cd backend
./deploy.sh
gunicorn payevo_proxy.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**📚 Leia `LEIA-ME-PRODUCAO.md` para mais detalhes!**

## 📝 Notas

- O frontend está na pasta `html/` e é servido automaticamente pelo Django
- A API está disponível em `http://localhost:8000/api/`
- O frontend está disponível em `http://localhost:8000/`
- O gateway padrão é **KorePay** (configurado nas settings)
- Para produção, use `settings_production.py` com variáveis de ambiente

## 🐛 Troubleshooting

### Erro: "Failed to fetch"
- Verifique se o servidor está rodando
- Verifique se a URL da API está correta (deve ser `/api/transactions/pix/`)
- Verifique o console do navegador para erros de CORS

### Erro: "Server misconfigured"
- Verifique se as credenciais do KorePay estão configuradas em `settings.py`
- Verifique se as variáveis de ambiente estão definidas

### Frontend não carrega
- Verifique se os arquivos estão na pasta `html/`
- Verifique se o Django está servindo arquivos estáticos corretamente

