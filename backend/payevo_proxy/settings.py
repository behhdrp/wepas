import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"corsheaders",
	"payments",
]

MIDDLEWARE = [
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.security.SecurityMiddleware",
	"whitenoise.middleware.WhiteNoiseMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "payevo_proxy.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	},
]

WSGI_APPLICATION = "payevo_proxy.wsgi.application"

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.sqlite3",
		"NAME": BASE_DIR / "db.sqlite3",
	}
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# Frontend files
FRONTEND_DIR = BASE_DIR.parent / "html"
STATICFILES_DIRS = [
	FRONTEND_DIR,
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # Temporary for debugging CORS issues
# CORS_ALLOWED_ORIGINS_STR = os.environ.get(
# 	"CORS_ALLOWED_ORIGINS",
# 	"http://localhost:3000,http://localhost:8000,http://localhost:8001,https://wepas.netlify.app"
# )
# CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_STR.split(",")]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
	"DELETE",
	"GET",
	"OPTIONS",
	"PATCH",
	"POST",
	"PUT",
]
CORS_ALLOW_HEADERS = [
	"accept",
	"accept-encoding",
	"authorization",
	"content-type",
	"dnt",
	"origin",
	"user-agent",
	"x-csrftoken",
	"x-requested-with",
]

# Payevo settings
PAYEVO_SECRET_KEY = os.environ.get("PAYEVO_SECRET_KEY", "sk_like_rBAnuKBBJmQ2R4CmrfkfA6ibP6mcmQ4XkqVh3URirYdhN3zg")
PAYEVO_BASE_URL = "https://apiv2.payevo.com.br/functions/v1"
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8001")

# UTMify
UTMIFY_TOKEN = os.environ.get("UTMIFY_TOKEN", "1cQVsDpeWzfUmScfzlKge3KAsFSusZGFg54l")
UTMIFY_ENDPOINT = os.environ.get("UTMIFY_ENDPOINT", "https://api.utmify.com.br/api-credentials/orders")

# Meta (Facebook) Conversions API
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
META_API_VERSION = "v21.0"
META_TEST_EVENT_CODE = os.environ.get("META_TEST_EVENT_CODE", "")
META_PIXELS = os.environ.get("META_PIXELS", "1377008160887444,850654324485411,2215968492258432").split(",")
META_PIXEL_TOKENS = {}
# Parse META_PIXEL_TOKENS do formato: "pixel1:token1,pixel2:token2"
meta_tokens_str = os.environ.get("META_PIXEL_TOKENS", "")
if meta_tokens_str:
	for pair in meta_tokens_str.split(","):
		if ":" in pair:
			pixel_id, token = pair.split(":", 1)
			META_PIXEL_TOKENS[pixel_id.strip()] = token.strip()
else:
	# Fallback para desenvolvimento (NÃO usar em produção!)
	META_PIXEL_TOKENS = {
		"2215968492258432": os.environ.get("META_TOKEN_2215968492258432", ""),
		"850654324485411": os.environ.get("META_TOKEN_850654324485411", ""),
		"1377008160887444": os.environ.get("META_TOKEN_1377008160887444", ""),
	}
	# Remove tokens vazios
	META_PIXEL_TOKENS = {k: v for k, v in META_PIXEL_TOKENS.items() if v}

# Korepay settings
KOREPAY_BASE_URL = os.environ.get("KOREPAY_BASE_URL", "https://api.korepay.com.br/v1")
KOREPAY_SECRET_KEY = os.environ.get("KOREPAY_SECRET_KEY", "sk_DNGMBjEbVvh4fviEGlh-9aPkgPVXhci6dSjvH85Oql-ltob1")
KOREPAY_PUBLIC_KEY = os.environ.get("KOREPAY_PUBLIC_KEY", "pk_dBeLGhigOmVI46RYUhU2xJIU9Yck2e0p_69a-HT-4xFTCyYZ")
KOREPAY_WITHDRAWAL_KEY = os.environ.get("KOREPAY_WITHDRAWAL_KEY", "wk_frH0Rw9gQHshmaJekYlbdxbOFqINL7YP0TXpwU6sulE6-8s-")
KOREPAY_COMPANY_ID = os.environ.get("KOREPAY_COMPANY_ID", "cb68e0a7-b04e-46eb-be97-46e84954debe")

# API Base URL (for client-side to know where to call)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")

