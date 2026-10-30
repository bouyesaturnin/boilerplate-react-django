from pathlib import Path
from datetime import timedelta
import os
import re
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Liste séparée par des virgules, sans éléments vides."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def admin_path(value):
    """Normalise DJANGO_ADMIN_PATH (sans barres superflues) et refuse les valeurs dangereuses."""
    segments = [segment for segment in value.strip().split("/") if segment]
    if not segments:
        return "admin"
    for segment in segments:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", segment):
            raise ImproperlyConfigured(
                "DJANGO_ADMIN_PATH ne doit contenir que des lettres, chiffres, tirets et underscores."
            )
    # L'admin capture toutes les URL sous son préfixe : il ne doit pas masquer l'API ni les statiques
    if segments[0].lower() in {"api", "static"}:
        raise ImproperlyConfigured("DJANGO_ADMIN_PATH ne peut pas commencer par 'api' ou 'static'.")
    return "/".join(segments)


# ── Sécurité ──────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Chemin de l'admin (défaut : admin). Un chemin non devinable réduit le bruit des robots,
# mais ne remplace ni l'authentification ni les permissions de l'admin Django.
ADMIN_PATH = admin_path(os.getenv("DJANGO_ADMIN_PATH", ""))

AUTH_USER_MODEL = "accounts.User"

# ── Applications ──────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "accounts",
    "core",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Base de données ───────────────────────────────────────────────────────────
# En production : définir DATABASE_URL dans .env (ex: postgresql://user:pass@host/db)
# En développement : SQLite utilisé par défaut

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Validation des mots de passe ──────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# ── Fichiers statiques ────────────────────────────────────────────────────────

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Django 5.1+ ignore STATICFILES_STORAGE : la configuration passe par STORAGES.
# "default" (fichiers utilisateur) garde le stockage disque standard.
# En production (DEBUG=False), `collectstatic` doit être lancé avant le démarrage (voir Procfile) :
# sans manifeste, les pages utilisant {% static %} (l'admin) renvoient une erreur 500.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── DRF ───────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Limitation de débit des endpoints d'authentification (ScopedRateThrottle, par IP).
    # Les compteurs sont dans le cache par défaut (mémoire locale) : chaque worker
    # Gunicorn a les siens. Ce n'est pas une protection contre une attaque distribuée.
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": "10/minute",
        "auth_register": "5/hour",
        "auth_refresh": "30/minute",
    },
    # Nombre de proxys de confiance devant Django, pour lire l'IP client dans
    # X-Forwarded-For. 0 = ignorer cet en-tête (falsifiable sans proxy).
    "NUM_PROXIES": int(os.getenv("DRF_NUM_PROXIES", "0")),
}

# ── JWT ───────────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# Origines HTTPS autorisées à soumettre des formulaires (admin) quand elles
# diffèrent du domaine servi, ex. https://app.exemple.fr
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# ── Proxy HTTPS ───────────────────────────────────────────────────────────────
# À activer uniquement derrière un proxy de confiance qui fixe X-Forwarded-Proto
# (Railway, Heroku, Nginx...). Sans proxy, l'en-tête serait falsifiable par le client.

if os.getenv("TRUST_PROXY_SSL_HEADER", "False") == "True":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Journalisation ────────────────────────────────────────────────────────────
# Avertissements et erreurs Django (dont les erreurs 500) vers la sortie standard,
# collectée par l'hébergeur. Les messages Django ne contiennent ni en-têtes, ni corps
# de requête, ni cookies : aucun mot de passe ni token n'y est écrit.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# ── Sécurité production ───────────────────────────────────────────────────────
# Ces paramètres s'activent automatiquement quand DEBUG=False

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000          # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Preload : engagement durable pour tout le domaine parent, à n'activer qu'en connaissance de cause
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
