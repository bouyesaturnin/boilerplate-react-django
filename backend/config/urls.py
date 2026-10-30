from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Chemin configurable par DJANGO_ADMIN_PATH (normalisé et validé dans settings.py)
    path(f"{settings.ADMIN_PATH}/", admin.site.urls),
    # Compatibilité : ancien endpoint de santé conservé
    path("api/", include("core.urls")),
    # API versionnée
    path("api/v1/", include("core.urls")),
    path("api/v1/auth/", include("accounts.urls")),
]
