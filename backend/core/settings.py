# backend/core/settings.py
from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

# ELIMINADO: load_dotenv() no debe usarse en producción. Las variables vienen del entorno.

BASE_DIR = Path(__file__).resolve().parent.parent

# Render inyectará esta variable. Si no existe, os.getenv devuelve None y Django fallará con un error claro.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# Esta es la forma correcta de detectar si estamos en Render.
IS_RENDER = 'RENDER' in os.environ
DEBUG = not IS_RENDER

ALLOWED_HOSTS = []
if IS_RENDER:
    RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Para desarrollo local
if not IS_RENDER:
    ALLOWED_HOSTS.append('127.0.0.1')
    ALLOWED_HOSTS.append('localhost')

INSTALLED_APPS = [
    "core_app",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic", # Esto está bien, no afecta producción
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "django_extensions",
    "corsheaders",
    # Propias
    "catalogo",
    "compras",
    "ventas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise Middleware - ¡La posición es importante!
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware", # Movido para estar antes de CommonMiddleware
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

# --- MODIFICACIÓN CLAVE ---
# Hacemos que la configuración de la base de datos falle ruidosamente si DATABASE_URL no está.
# No más fallback silencioso a SQLite en producción.
if IS_RENDER:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
        )
    }


AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# Esta es la carpeta donde `collectstatic` pondrá todos los archivos estáticos.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Esto le dice a WhiteNoise que sirva archivos comprimidos para un mejor rendimiento.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend", "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"],
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

# --- Configuración de CORS ---
CORS_ALLOWED_ORIGINS = []
if IS_RENDER:
    RENDER_FRONTEND_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_FRONTEND_URL:
        CORS_ALLOWED_ORIGINS.append(RENDER_FRONTEND_URL)

if not IS_RENDER:
    CORS_ALLOWED_ORIGINS.append("http://localhost:5173")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["accept", "authorization", "content-type", "user-agent", "x-csrftoken", "x-requested-with", "x-local-id"]