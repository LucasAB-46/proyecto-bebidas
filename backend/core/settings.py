# backend/core/settings.py

from pathlib import Path
import os
from datetime import timedelta
import dj_database_url
from corsheaders.defaults import default_headers  # <-- agregado

BASE_DIR = Path(__file__).resolve().parent.parent

# === Runtime flags ===
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY and not DEBUG:
    raise RuntimeError("Falta DJANGO_SECRET_KEY en variables de entorno")

def env_list(name: str, default=None):
    """
    Lee una variable de entorno tipo 'a,b,c' y devuelve ['a','b','c'].
    Si no existe devuelve default o [].
    """
    val = os.getenv(name)
    if not val:
        return default or []
    return [x.strip() for x in val.split(",") if x.strip()]

# === Hosts / CSRF / CORS ===

# ALLOWED_HOSTS:
# - usamos APP_ALLOWED_HOSTS de Railway
# - si no hay, en DEBUG usamos localhost / 127.0.0.1
# - en prod si no hay, fallback "*"
DEFAULT_HOSTS = ["127.0.0.1", "localhost"] if DEBUG else ["*"]
ALLOWED_HOSTS = env_list("APP_ALLOWED_HOSTS", DEFAULT_HOSTS)

# Permite que Django sepa que está detrás de proxy HTTPS (Railway)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF_TRUSTED_ORIGINS:
# - dominios que pueden mandar POST/PUT/DELETE con credenciales
# - leemos APP_CSRF_TRUSTED_ORIGINS de Railway
CSRF_TRUSTED_ORIGINS = env_list("APP_CSRF_TRUSTED_ORIGINS", [])
if DEBUG and not CSRF_TRUSTED_ORIGINS:
    # fallback útil en dev
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# CORS_ALLOWED_ORIGINS:
# - orígenes desde donde aceptamos requests del browser (Vercel, localhost)
CORS_ALLOWED_ORIGINS = env_list("APP_CORS_ALLOW_ORIGINS", [])
if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# Permitimos credenciales (Authorization header / JWT)
CORS_ALLOW_CREDENTIALS = True

# Permitimos también nuestro header custom "X-Local-ID"
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-local-id",
]

INSTALLED_APPS = [
    "core_app",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "corsheaders",

    # Propias
    "catalogo",
    "compras",
    "ventas",
    "reportes",
]

# Solo en dev si está instalado django-extensions
if DEBUG:
    try:
        import django_extensions  # noqa: F401
        INSTALLED_APPS.append("django_extensions")
    except Exception:
        pass

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise sirve estáticos en producción sin depender de nginx
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    # corsheaders SIEMPRE tiene que ir antes de CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

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

WSGI_APPLICATION = "core.wsgi.application"

# === Base de datos ===
# Si tenemos DATABASE_URL (Railway/Postgres), la usamos.
# Si no, usamos SQLite local (dev).
if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API – Bebidas",
    "VERSION": "0.1.0",
}
