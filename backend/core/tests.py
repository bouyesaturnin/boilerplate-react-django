import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APITestCase
from rest_framework import status


class HealthCheckTests(APITestCase):

    def test_health_check_returns_200(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_v1_returns_200(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_returns_expected_body(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.data['status'], 'ok')
        self.assertIn('message', response.data)

    def test_health_check_is_public(self):
        """L'endpoint de santé ne nécessite pas d'authentification."""
        response = self.client.get('/api/v1/health/')
        self.assertNotIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


# ── Réglages pilotés par l'environnement ──────────────────────────────────────
# Les réglages sont lus au démarrage : chaque cas est vérifié dans un processus Django neuf.
# Toutes les variables sont fixées explicitement pour que le .env local n'influence pas les tests.

PRODUCTION_ENV = {
    'SECRET_KEY': 'cle-factice-pour-tests-de-reglages',
    'DEBUG': 'False',
    'ALLOWED_HOSTS': 'app.exemple.fr',
    'CORS_ALLOWED_ORIGINS': '',
    'CSRF_TRUSTED_ORIGINS': '',
    'TRUST_PROXY_SSL_HEADER': 'False',
    'SECURE_HSTS_PRELOAD': 'False',
    'DJANGO_ADMIN_PATH': '',
    'DRF_NUM_PROXIES': '0',
    'DATABASE_URL': '',
}

SETTINGS_PROBE = """
import json, django
django.setup()
from django.conf import settings as s
from django.urls import Resolver404, resolve

def resolves(path):
    try:
        resolve(path)
        return True
    except Resolver404:
        return False

print(json.dumps({
    'debug': s.DEBUG,
    'proxy_header': getattr(s, 'SECURE_PROXY_SSL_HEADER', None),
    'ssl_redirect': s.SECURE_SSL_REDIRECT,
    'hsts_seconds': s.SECURE_HSTS_SECONDS,
    'hsts_preload': s.SECURE_HSTS_PRELOAD,
    'session_cookie_secure': s.SESSION_COOKIE_SECURE,
    'csrf_cookie_secure': s.CSRF_COOKIE_SECURE,
    'num_proxies': s.REST_FRAMEWORK['NUM_PROXIES'],
    'allowed_hosts': s.ALLOWED_HOSTS,
    'cors_origins': s.CORS_ALLOWED_ORIGINS,
    'csrf_trusted_origins': s.CSRF_TRUSTED_ORIGINS,
    'storage_default': s.STORAGES['default']['BACKEND'],
    'storage_static': s.STORAGES['staticfiles']['BACKEND'],
    'admin_path': s.ADMIN_PATH,
    'admin_default_resolves': resolves('/admin/login/'),
    'admin_custom_resolves': resolves('/gestion-test/login/'),
    'admin_nested_resolves': resolves('/espace/gestion/login/'),
    'api_resolves': resolves('/api/v1/health/'),
}))
"""


def run_with_env(args, **overrides):
    env = {**os.environ, **PRODUCTION_ENV, **overrides,
           'DJANGO_SETTINGS_MODULE': 'config.settings', 'PYTHONDONTWRITEBYTECODE': '1'}
    return subprocess.run([sys.executable, *args], cwd=settings.BASE_DIR, env=env,
                          capture_output=True, text=True, timeout=120)


def probe_settings(**overrides):
    result = run_with_env(['-c', SETTINGS_PROBE], **overrides)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout.strip().splitlines()[-1])


class ProductionSettingsTests(SimpleTestCase):

    def test_production_defaults_are_safe(self):
        values = probe_settings()
        self.assertFalse(values['debug'])
        self.assertIsNone(values['proxy_header'])
        self.assertTrue(values['ssl_redirect'])
        self.assertEqual(values['hsts_seconds'], 31536000)
        self.assertFalse(values['hsts_preload'])
        self.assertTrue(values['session_cookie_secure'])
        self.assertTrue(values['csrf_cookie_secure'])
        self.assertEqual(values['num_proxies'], 0)
        self.assertEqual(values['csrf_trusted_origins'], [])
        self.assertEqual(values['cors_origins'], [])

    def test_development_mode_disables_https_enforcement(self):
        values = probe_settings(DEBUG='True')
        self.assertFalse(values['ssl_redirect'])
        self.assertEqual(values['hsts_seconds'], 0)
        self.assertIsNone(values['proxy_header'])

    def test_proxy_ssl_header_is_opt_in(self):
        values = probe_settings(TRUST_PROXY_SSL_HEADER='True')
        self.assertEqual(values['proxy_header'], ['HTTP_X_FORWARDED_PROTO', 'https'])
        self.assertTrue(values['ssl_redirect'])

    def test_proxy_ssl_header_ignores_other_values(self):
        self.assertIsNone(probe_settings(TRUST_PROXY_SSL_HEADER='yes')['proxy_header'])

    def test_hsts_preload_is_opt_in(self):
        self.assertTrue(probe_settings(SECURE_HSTS_PRELOAD='True')['hsts_preload'])

    def test_lists_ignore_blank_entries(self):
        values = probe_settings(
            ALLOWED_HOSTS='a.exemple.fr, ,b.exemple.fr,',
            CORS_ALLOWED_ORIGINS=',https://front.exemple.fr,',
            CSRF_TRUSTED_ORIGINS=' https://a.exemple.fr ,https://b.exemple.fr',
        )
        self.assertEqual(values['allowed_hosts'], ['a.exemple.fr', 'b.exemple.fr'])
        self.assertEqual(values['cors_origins'], ['https://front.exemple.fr'])
        self.assertEqual(values['csrf_trusted_origins'], ['https://a.exemple.fr', 'https://b.exemple.fr'])

    def test_system_check_passes_with_empty_lists(self):
        result = run_with_env(['manage.py', 'check'], CORS_ALLOWED_ORIGINS='', CSRF_TRUSTED_ORIGINS='')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_static_and_media_storages(self):
        values = probe_settings()
        self.assertEqual(values['storage_static'], 'whitenoise.storage.CompressedManifestStaticFilesStorage')
        self.assertEqual(values['storage_default'], 'django.core.files.storage.FileSystemStorage')


class AdminPathSettingsTests(SimpleTestCase):

    def test_default_admin_path(self):
        values = probe_settings()
        self.assertEqual(values['admin_path'], 'admin')
        self.assertTrue(values['admin_default_resolves'])
        self.assertTrue(values['api_resolves'])

    def test_custom_admin_path_is_normalized(self):
        values = probe_settings(DJANGO_ADMIN_PATH=' /gestion-test/ ')
        self.assertEqual(values['admin_path'], 'gestion-test')
        self.assertTrue(values['admin_custom_resolves'])
        self.assertFalse(values['admin_default_resolves'])
        self.assertTrue(values['api_resolves'])

    def test_nested_admin_path_without_double_slashes(self):
        values = probe_settings(DJANGO_ADMIN_PATH='espace//gestion/')
        self.assertEqual(values['admin_path'], 'espace/gestion')
        self.assertTrue(values['admin_nested_resolves'])

    def test_invalid_admin_paths_are_refused(self):
        for value in ('../gestion', 'ges tion', 'gestion?x=1', 'gestion.php', 'gest%69on'):
            with self.subTest(value=value):
                result = run_with_env(['-c', SETTINGS_PROBE], DJANGO_ADMIN_PATH=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ImproperlyConfigured', result.stderr)

    def test_admin_path_cannot_shadow_api_or_static(self):
        for value in ('api', 'API/gestion', 'static'):
            with self.subTest(value=value):
                result = run_with_env(['-c', SETTINGS_PROBE], DJANGO_ADMIN_PATH=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ImproperlyConfigured', result.stderr)


class LoggingSettingsTests(SimpleTestCase):

    def test_django_warnings_and_errors_go_to_console(self):
        django_logger = settings.LOGGING['loggers']['django']
        self.assertEqual(django_logger['level'], 'WARNING')
        self.assertEqual(django_logger['handlers'], ['console'])
        self.assertEqual(settings.LOGGING['handlers']['console']['class'], 'logging.StreamHandler')
        self.assertEqual(logging.getLogger('django.request').getEffectiveLevel(), logging.WARNING)


class ProcfileTests(SimpleTestCase):

    def test_collectstatic_runs_before_gunicorn(self):
        procfile = (Path(settings.BASE_DIR) / 'Procfile').read_text(encoding='utf-8')
        web = next(line for line in procfile.splitlines() if line.startswith('web:'))
        self.assertIn('collectstatic --noinput', web)
        self.assertLess(web.index('collectstatic'), web.index('gunicorn'))
        self.assertNotIn('migrate', web, 'les migrations relèvent de la commande de pré-déploiement')


# ── Administration et fichiers statiques ──────────────────────────────────────

@override_settings(STORAGES={
    **settings.STORAGES,
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class AdminAvailabilityTests(APITestCase):
    """Sans collectstatic (développement), l'admin reste servi avec un stockage statique simple."""

    def test_admin_login_page_is_served(self):
        self.assertEqual(resolve('/admin/login/').app_name, 'admin')
        response = self.client.get('/admin/login/', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_index_requires_login(self):
        response = self.client.get('/admin/', secure=True)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/admin/login/', response['Location'])


class CollectedStaticFilesTests(APITestCase):
    """Chaîne de production simulée en local : collectstatic, manifeste, puis service par WhiteNoise."""

    def setUp(self):
        self.static_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.static_root.cleanup)
        override = override_settings(STATIC_ROOT=self.static_root.name)
        override.enable()
        self.addCleanup(override.disable)
        call_command('collectstatic', interactive=False, verbosity=0)

    def test_manifest_and_compressed_files_are_generated(self):
        root = Path(self.static_root.name)
        self.assertTrue((root / 'staticfiles.json').exists())
        css_files = [p.name for p in (root / 'admin' / 'css').iterdir()]
        self.assertTrue(any(name.endswith('.css.gz') for name in css_files))
        self.assertTrue(any(name.endswith('.css.br') for name in css_files))

    def test_admin_page_references_hashed_static_served_by_whitenoise(self):
        response = self.client.get('/admin/login/', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        css_url = re.search(r'/static/admin/css/base\.[0-9a-f]{12}\.css', response.content.decode())
        self.assertIsNotNone(css_url, "l'admin doit référencer la feuille de style hachée")
        css = self.client.get(css_url.group(0), secure=True)
        # Réponse servie en streaming depuis un fichier ouvert : la fermer libère le fichier
        # (sinon Windows refuse de supprimer le dossier temporaire).
        self.addCleanup(css.close)
        self.assertEqual(css.status_code, status.HTTP_200_OK)
        self.assertIn('immutable', css['Cache-Control'])
