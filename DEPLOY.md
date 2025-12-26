# 🚀 Guia de Deploy - Projeto Kore

## ⚠️ IMPORTANTE: Antes de Subir

O projeto **NÃO está 100% pronto** para produção. Você precisa:

1. ✅ **Configurar variáveis de ambiente** (obrigatório)
2. ✅ **Configurar banco PostgreSQL** (recomendado)
3. ✅ **Configurar servidor web** (Nginx/Apache)
4. ✅ **Configurar SSL/HTTPS**
5. ✅ **Remover credenciais hardcoded** do código

---

## 📋 Passo a Passo para Deploy

### 1. Preparar Variáveis de Ambiente

Copie o arquivo de exemplo:
```bash
cp env.example .env
```

Edite o arquivo `.env` com suas credenciais reais:

```bash
# OBRIGATÓRIO
DJANGO_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
CORS_ALLOWED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

# BANCO DE DADOS (PostgreSQL recomendado)
DB_NAME=kore_db
DB_USER=kore_user
DB_PASSWORD=senha-forte-aqui
DB_HOST=localhost
DB_PORT=5432

# GATEWAY DE PAGAMENTO
KOREPAY_SECRET_KEY=sua-chave-real-korepay
KOREPAY_COMPANY_ID=seu-company-id-real
PAYEVO_SECRET_KEY=sua-chave-real-payevo

# INTEGRAÇÕES
UTMIFY_TOKEN=seu-token-real-utmify
META_ACCESS_TOKEN=seu-token-real-meta
META_PIXELS=1377008160887444,850654324485411,2215968492258432
META_PIXEL_TOKENS=pixel1:token1,pixel2:token2,pixel3:token3

# URL PÚBLICA
PUBLIC_BASE_URL=https://seu-dominio.com

# SSL
SECURE_SSL_REDIRECT=True
```

### 2. Instalar Dependências

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar Banco de Dados PostgreSQL

```bash
# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE kore_db;
CREATE USER kore_user WITH PASSWORD 'sua-senha';
GRANT ALL PRIVILEGES ON DATABASE kore_db TO kore_user;
\q
```

### 4. Executar Migrações

```bash
export DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production
# Carregar variáveis do .env (use python-decouple ou export manual)
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Testar Configuração

```bash
python manage.py check --deploy
```

### 6. Iniciar com Gunicorn

```bash
gunicorn payevo_proxy.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --env DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production
```

### 7. Configurar Nginx (Recomendado)

Crie `/etc/nginx/sites-available/kore`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /path/to/kore/backend/staticfiles/;
        expires 30d;
    }

    # Frontend e API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar:
```bash
sudo ln -s /etc/nginx/sites-available/kore /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Configurar Systemd (Opcional)

Crie `/etc/systemd/system/kore.service`:

```ini
[Unit]
Description=Kore Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/kore/backend
Environment="DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production"
EnvironmentFile=/path/to/kore/.env
ExecStart=/path/to/kore/backend/.venv/bin/gunicorn payevo_proxy.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kore
sudo systemctl start kore
```

---

## ✅ Checklist Final

Antes de considerar o deploy completo, verifique:

- [ ] Todas as variáveis de ambiente configuradas
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] `CORS_ALLOWED_ORIGINS` configurado
- [ ] PostgreSQL configurado (não SQLite)
- [ ] SSL/HTTPS configurado
- [ ] Credenciais removidas do código
- [ ] Logs configurados
- [ ] Backup do banco de dados configurado
- [ ] Monitoramento configurado
- [ ] Testes realizados em ambiente de staging

---

## 🔒 Segurança

**CRÍTICO**: As seguintes credenciais ainda estão hardcoded no `settings.py`:

- `PAYEVO_SECRET_KEY` (linha 101)
- `UTMIFY_TOKEN` (linha 106)
- `KOREPAY_SECRET_KEY` (linha 126)
- `KOREPAY_COMPANY_ID` (linha 127)
- `META_PIXEL_TOKENS` (linhas 118-122)

**AÇÃO NECESSÁRIA**: Remova esses valores e use apenas variáveis de ambiente em produção!

---

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs: `tail -f /var/log/kore/django.log`
2. Verifique o status do serviço: `sudo systemctl status kore`
3. Teste a configuração: `python manage.py check --deploy`

---

## 🎯 Resumo Rápido

```bash
# 1. Configurar .env
cp env.example .env
nano .env  # Editar com suas credenciais

# 2. Instalar e configurar
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 3. Migrar banco
export DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production
python manage.py migrate
python manage.py collectstatic --noinput

# 4. Iniciar
gunicorn payevo_proxy.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

**⚠️ LEMBRE-SE**: O projeto usa `settings_production.py` apenas quando `DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production` está definido!

