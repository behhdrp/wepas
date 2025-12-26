"""
Configurações de Produção
Use este arquivo em produção definindo: DJANGO_SETTINGS_MODULE=payevo_proxy.settings_production
"""
import os
from pathlib import Path

# BASE_DIR deve ser definido antes de importar settings
BASE_DIR = Path(__file__).resolve().parent.parent

# Importa todas as configurações base
from .settings import *

# ============ SEGURANÇA ============

# DEBUG deve ser False em produção
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# SECRET_KEY deve ser fornecida via variável de ambiente
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
	raise ValueError("DJANGO_SECRET_KEY deve ser definida em produção!")

# ALLOWED_HOSTS deve ser específico
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
	raise ValueError("ALLOWED_HOSTS deve ser definido em produção! Ex: ALLOWED_HOSTS=example.com,www.example.com")

# ============ CORS ============

# CORS restrito a domínios específicos
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS if origin.strip()]

if not CORS_ALLOWED_ORIGINS:
	raise ValueError("CORS_ALLOWED_ORIGINS deve ser definido em produção! Ex: CORS_ALLOWED_ORIGINS=https://example.com,https://www.example.com")

# ============ BANCO DE DADOS ============

# Para produção, use PostgreSQL ao invés de SQLite
DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.postgresql",
		"NAME": os.environ.get("DB_NAME", "kore_db"),
		"USER": os.environ.get("DB_USER", "kore_user"),
		"PASSWORD": os.environ.get("DB_PASSWORD", ""),
		"HOST": os.environ.get("DB_HOST", "localhost"),
		"PORT": os.environ.get("DB_PORT", "5432"),
		"OPTIONS": {
			"connect_timeout": 10,
		},
	}
}

# Se DB_PASSWORD não estiver definido, usa SQLite (não recomendado para produção)
if not os.environ.get("DB_PASSWORD"):
	print("⚠️  AVISO: DB_PASSWORD não definido. Usando SQLite (não recomendado para produção)")
	DATABASES = {
		"default": {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME": BASE_DIR / "db.sqlite3",
		}
	}

# ============ SEGURANÇA HTTP ============

# Headers de segurança
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ============ CREDENCIAIS (DEVEM VIR DE VARIÁVEIS DE AMBIENTE) ============

# Payevo
PAYEVO_SECRET_KEY = os.environ.get("PAYEVO_SECRET_KEY", "")

# KorePay
KOREPAY_SECRET_KEY = os.environ.get("KOREPAY_SECRET_KEY", "")
KOREPAY_PUBLIC_KEY = os.environ.get("KOREPAY_PUBLIC_KEY", "")
KOREPAY_WITHDRAWAL_KEY = os.environ.get("KOREPAY_WITHDRAWAL_KEY", "")
KOREPAY_COMPANY_ID = os.environ.get("KOREPAY_COMPANY_ID", "")

# UTMify
UTMIFY_TOKEN = os.environ.get("UTMIFY_TOKEN", "")

# Meta
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
META_PIXEL_TOKENS = {}
# Parse META_PIXEL_TOKENS do formato: "pixel1:token1,pixel2:token2"
meta_tokens_str = os.environ.get("META_PIXEL_TOKENS", "")
if meta_tokens_str:
	for pair in meta_tokens_str.split(","):
		if ":" in pair:
			pixel_id, token = pair.split(":", 1)
			META_PIXEL_TOKENS[pixel_id.strip()] = token.strip()

# ============ LOGGING ============

# Configurar logging
LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"verbose": {
			"format": "{levelname} {asctime} {module} {message}",
			"style": "{",
		},
	},
	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
			"formatter": "verbose",
		},
	},
	"root": {
		"handlers": ["console"],
		"level": os.environ.get("LOG_LEVEL", "INFO"),
	},
	"loggers": {
		"django": {
			"handlers": ["console"],
			"level": os.environ.get("LOG_LEVEL", "INFO"),
			"propagate": False,
		},
		"payments": {
			"handlers": ["console"],
			"level": "INFO",
			"propagate": False,
		},
	},
}

# Adicionar handler de arquivo apenas se LOG_FILE estiver definido
log_file_path = os.environ.get("LOG_FILE", "")
if log_file_path:
	try:
		log_dir = Path(log_file_path).parent
		log_dir.mkdir(parents=True, exist_ok=True)
		LOGGING["handlers"]["file"] = {
			"class": "logging.handlers.RotatingFileHandler",
			"filename": log_file_path,
			"maxBytes": 1024 * 1024 * 10,  # 10MB
			"backupCount": 5,
			"formatter": "verbose",
		}
		LOGGING["root"]["handlers"].append("file")
		LOGGING["loggers"]["django"]["handlers"].append("file")
		LOGGING["loggers"]["payments"]["handlers"].append("file")
	except Exception:
		pass  # Se não conseguir criar, usa apenas console

# Criar diretório de logs se necessário (já feito acima se LOG_FILE estiver definido)

# ============ STATIC FILES ============

# Em produção, servir arquivos estáticos com nginx/apache
STATIC_ROOT = os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles")
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ============ VALIDAÇÕES ============

# Validação de senhas (se houver autenticação)
AUTH_PASSWORD_VALIDATORS = [
	{
		"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
	},
	{
		"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
		"OPTIONS": {
			"min_length": 8,
		},
	},
	{
		"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
	},
	{
		"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
	},
]

# ============ PERFORMANCE ============

# Cache (use Redis em produção)
redis_url = os.environ.get("REDIS_URL", "")
if redis_url:
	try:
		import django_redis
		CACHES = {
			"default": {
				"BACKEND": "django_redis.cache.RedisCache",
				"LOCATION": redis_url,
				"OPTIONS": {
					"CLIENT_CLASS": "django_redis.client.DefaultClient",
				},
				"KEY_PREFIX": "kore",
				"TIMEOUT": 300,
			}
		}
	except ImportError:
		print("⚠️  django-redis não instalado. Usando cache em memória.")
		CACHES = {
			"default": {
				"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
			}
		}
else:
	# Se Redis não estiver configurado, usa cache em memória
	CACHES = {
		"default": {
			"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
		}
	}

# ============ EMAIL (se necessário) ============

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

