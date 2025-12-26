# Payevo Proxy (Django)

Simple Django API that proxies Payevo transactions to keep the secret key on the server.

## Setup

1) Create and activate a virtualenv (PowerShell example):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2) Install requirements:

```bash
pip install -r backend/requirements.txt
```

3) Set environment variables (PowerShell):

```bash
$env:DJANGO_DEBUG="1"
$env:PAYEVO_SECRET_KEY="YOUR_SECRET_KEY_HERE"
$env:DJANGO_SECRET_KEY="change-me"
$env:PUBLIC_BASE_URL="http://localhost:8000"  # usado para montar o postbackUrl enviado à Payevo
$env:UTMIFY_TOKEN="SUA_CHAVE_DA_UTMIFY"
```

4) Run server:

```bash
python backend/manage.py migrate
python backend/manage.py runserver 0.0.0.0:8000
```

## Endpoint

POST `http://localhost:8000/api/transactions/pix/`

Body: same JSON as Payevo `transactions` endpoint. The server will forward it with Basic auth.

Response: JSON returned by Payevo (including `pix.qrcode`, `expirationDate`, `receiptUrl` if provided).

### Webhook (postback) from Payevo

Configure Payevo to POST to:

`{PUBLIC_BASE_URL}/api/postbacks/payevo/`

The server enviará um evento para a UTMify quando `status` for `paid`.

### UTMify

O servidor envia pedidos para:
`https://api.utmify.com.br/api-credentials/orders` (header `x-api-token: UTMIFY_TOKEN`)

Estados enviados:
- Ao criar transação Pix: `status: waiting_payment` (Pix gerado)
- No postback `paid`: `status: paid` (Pix pago)


