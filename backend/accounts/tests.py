import logging
from datetime import timedelta
from unittest import mock

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()

REGISTER_URL = '/api/v1/auth/register/'
LOGIN_URL    = '/api/v1/auth/login/'
REFRESH_URL  = '/api/v1/auth/token/refresh/'
LOGOUT_URL   = '/api/v1/auth/logout/'
ME_URL       = '/api/v1/auth/me/'

VALID_USER = {
    'email': 'test@example.com',
    'username': 'testuser',
    'password': 'securepass123',
}


class AuthAPITestCase(APITestCase):
    """Vide le cache avant chaque test : les compteurs de limitation de débit y sont stockés."""

    def setUp(self):
        cache.clear()


class RegisterTests(AuthAPITestCase):

    def test_register_success(self):
        response = self.client.post(REGISTER_URL, VALID_USER)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], VALID_USER['email'])

    def test_register_creates_user_in_database(self):
        self.client.post(REGISTER_URL, VALID_USER)
        self.assertTrue(User.objects.filter(email=VALID_USER['email']).exists())

    def test_register_password_not_returned(self):
        response = self.client.post(REGISTER_URL, VALID_USER)
        self.assertNotIn('password', response.data.get('user', {}))

    def test_register_duplicate_email_fails(self):
        self.client.post(REGISTER_URL, VALID_USER)
        response = self.client.post(REGISTER_URL, VALID_USER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_fails(self):
        data = {**VALID_USER, 'password': '1234'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_fails(self):
        data = {'username': 'testuser', 'password': 'securepass123'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        User.objects.create_user(
            email=VALID_USER['email'],
            username=VALID_USER['username'],
            password=VALID_USER['password'],
        )

    def test_login_success(self):
        response = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'],
            'password': VALID_USER['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'],
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email_fails(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'securepass123',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        User.objects.create_user(
            email=VALID_USER['email'],
            username=VALID_USER['username'],
            password=VALID_USER['password'],
        )
        login = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'],
            'password': VALID_USER['password'],
        })
        self.refresh_token = login.data['refresh']

    def test_refresh_returns_new_access_token(self):
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_with_invalid_token_fails(self):
        response = self.client.post(REFRESH_URL, {'refresh': 'invalid.token.here'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            email=VALID_USER['email'],
            username=VALID_USER['username'],
            password=VALID_USER['password'],
        )
        login = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'],
            'password': VALID_USER['password'],
        })
        self.access_token = login.data['access']
        self.refresh_token = login.data['refresh']

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_me_returns_profile(self):
        self._auth()
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], VALID_USER['email'])
        self.assertEqual(response.data['username'], VALID_USER['username'])

    def test_me_unauthenticated_returns_401(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_updates_profile(self):
        self._auth()
        response = self.client.patch(ME_URL, {'first_name': 'Alice'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alice')

    def test_me_patch_cannot_change_email(self):
        self._auth()
        self.client.patch(ME_URL, {'email': 'hacker@example.com'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, VALID_USER['email'])


class LogoutTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        User.objects.create_user(
            email=VALID_USER['email'],
            username=VALID_USER['username'],
            password=VALID_USER['password'],
        )
        login = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'],
            'password': VALID_USER['password'],
        })
        self.access_token = login.data['access']
        self.refresh_token = login.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_logout_success(self):
        response = self.client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        self.client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.client.credentials()
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_fails(self):
        response = self.client.post(LOGOUT_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated_fails(self):
        self.client.credentials()
        response = self.client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def create_user(email=VALID_USER['email'], username=VALID_USER['username']):
    return User.objects.create_user(email=email, username=username, password=VALID_USER['password'])


class PasswordValidationTests(AuthAPITestCase):
    """Les validateurs AUTH_PASSWORD_VALIDATORS s'appliquent à l'inscription."""

    def assert_password_rejected(self, data):
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertIsInstance(response.data['password'], list)
        self.assertTrue(all(isinstance(message, str) and message for message in response.data['password']))
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertFalse(User.objects.filter(email=data['email']).exists())
        return response

    def test_common_password_rejected(self):
        self.assert_password_rejected({**VALID_USER, 'password': 'password123'})

    def test_numeric_password_rejected(self):
        self.assert_password_rejected({**VALID_USER, 'password': '84736251'})

    def test_password_similar_to_username_rejected(self):
        self.assert_password_rejected({**VALID_USER, 'password': 'testuser2024'})

    def test_password_similar_to_email_rejected(self):
        self.assert_password_rejected(
            {'email': 'jeanmartin@example.com', 'username': 'jmartin', 'password': 'jeanmartin1'}
        )

    def test_strong_password_accepted_and_hashed(self):
        data = {'email': 'robuste@example.com', 'username': 'robuste', 'password': 'Vx7#qLm2-Tr9!wKe'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        user = User.objects.get(email=data['email'])
        self.assertNotEqual(user.password, data['password'])
        self.assertTrue(user.check_password(data['password']))


class LogoutAfterRotationTests(AuthAPITestCase):
    """Contrat API sur lequel repose le frontend : après rotation, seul le refresh token courant est révocable."""

    def setUp(self):
        super().setUp()
        create_user()
        login = self.client.post(LOGIN_URL, {'email': VALID_USER['email'], 'password': VALID_USER['password']})
        self.initial_refresh = login.data['refresh']
        rotated = self.client.post(REFRESH_URL, {'refresh': self.initial_refresh}).data
        self.rotated_refresh = rotated['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {rotated['access']}")

    def test_stale_refresh_token_cannot_logout(self):
        response = self.client.post(LOGOUT_URL, {'refresh': self.initial_refresh})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_refresh_token_logout_revokes_it(self):
        response = self.client.post(LOGOUT_URL, {'refresh': self.rotated_refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()
        response = self.client.post(REFRESH_URL, {'refresh': self.rotated_refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NonExpiringCache:
    """Cache des compteurs sans expiration réelle, propre à chaque test."""

    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, timeout=None):
        self.data[key] = value


class ThrottleTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        # Horloge figée : sur une machine lente, 10 hachages de mot de passe peuvent dépasser
        # la fenêtre d'une minute et rendre le résultat dépendant de la vitesse d'exécution.
        clock = mock.patch.object(SimpleRateThrottle, 'timer', lambda self: 1_000_000.0)
        clock.start()
        self.addCleanup(clock.stop)
        # Cache sans expiration et neuf à chaque test : le cache local expire selon l'horloge
        # réelle (une mise en veille suffit) et ne doit pas être partagé entre tests.
        counters = mock.patch.object(SimpleRateThrottle, 'cache', NonExpiringCache())
        counters.start()
        self.addCleanup(counters.stop)
        create_user()
        self.bad_credentials = {'email': VALID_USER['email'], 'password': 'wrongpassword'}

    def test_login_limited_to_10_per_minute(self):
        for _ in range(10):
            response = self.client.post(LOGIN_URL, self.bad_credentials)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(LOGIN_URL, self.bad_credentials)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_blocked_even_with_valid_credentials_once_limited(self):
        for _ in range(10):
            self.client.post(LOGIN_URL, self.bad_credentials)
        response = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'], 'password': VALID_USER['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_works_normally_below_limit(self):
        response = self.client.post(LOGIN_URL, {
            'email': VALID_USER['email'], 'password': VALID_USER['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_limited_to_5_per_hour(self):
        for i in range(5):
            response = self.client.post(REGISTER_URL, {
                'email': f'user{i}@example.com', 'username': f'user{i}', 'password': 'securepass123',
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(REGISTER_URL, {
            'email': 'user5@example.com', 'username': 'user5', 'password': 'securepass123',
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(User.objects.filter(email='user5@example.com').exists())

    def test_refresh_limited_to_30_per_minute(self):
        for _ in range(30):
            response = self.client.post(REFRESH_URL, {'refresh': 'invalid.token.here'})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(REFRESH_URL, {'refresh': 'invalid.token.here'})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_limit_is_per_client_ip(self):
        for _ in range(10):
            self.client.post(LOGIN_URL, self.bad_credentials, REMOTE_ADDR='198.51.100.1')
        other_ip = self.client.post(LOGIN_URL, self.bad_credentials, REMOTE_ADDR='198.51.100.2')
        self.assertEqual(other_ip.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_spoofed_forwarded_for_header_does_not_bypass_limit_by_default(self):
        for i in range(10):
            self.client.post(LOGIN_URL, self.bad_credentials, HTTP_X_FORWARDED_FOR=f'203.0.113.{i}')
        response = self.client.post(LOGIN_URL, self.bad_credentials, HTTP_X_FORWARDED_FOR='203.0.113.99')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(REST_FRAMEWORK={**settings.REST_FRAMEWORK, 'NUM_PROXIES': 1})
    def test_behind_one_proxy_client_ip_comes_from_last_forwarded_address(self):
        proxy = {'REMOTE_ADDR': '10.0.0.254'}
        for i in range(10):
            self.client.post(LOGIN_URL, self.bad_credentials,
                             HTTP_X_FORWARDED_FOR=f'1.2.3.{i}, 203.0.113.5', **proxy)
        same_client = self.client.post(LOGIN_URL, self.bad_credentials,
                                       HTTP_X_FORWARDED_FOR='9.9.9.9, 203.0.113.5', **proxy)
        self.assertEqual(same_client.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        other_client = self.client.post(LOGIN_URL, self.bad_credentials,
                                        HTTP_X_FORWARDED_FOR='203.0.113.6', **proxy)
        self.assertEqual(other_client.status_code, status.HTTP_401_UNAUTHORIZED)


def expired_token(token_class, user):
    token = token_class.for_user(user)
    token.set_exp(lifetime=-timedelta(seconds=1))
    return str(token)


class RegisterInputTests(AuthAPITestCase):

    def test_register_invalid_email_fails(self):
        response = self.client.post(REGISTER_URL, {**VALID_USER, 'email': 'pas-un-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertFalse(User.objects.exists())


class LoginSecurityTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        create_user()

    def test_login_errors_do_not_reveal_whether_account_exists(self):
        wrong_password = self.client.post(LOGIN_URL, {'email': VALID_USER['email'], 'password': 'wrongpassword'})
        unknown_email = self.client.post(LOGIN_URL, {'email': 'nobody@example.com', 'password': 'wrongpassword'})
        self.assertEqual(wrong_password.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(wrong_password.data, unknown_email.data)

    def test_login_inactive_user_fails(self):
        User.objects.filter(email=VALID_USER['email']).update(is_active=False)
        response = self.client.post(LOGIN_URL, {'email': VALID_USER['email'], 'password': VALID_USER['password']})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenLifecycleTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.user = create_user()
        login = self.client.post(LOGIN_URL, {'email': VALID_USER['email'], 'password': VALID_USER['password']})
        self.refresh_token = login.data['refresh']

    def test_refresh_rotates_refresh_token(self):
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertIn('refresh', response.data)
        self.assertNotEqual(response.data['refresh'], self.refresh_token)

    def test_old_refresh_token_rejected_after_rotation(self):
        self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_refresh_token_works_after_rotation(self):
        rotated = self.client.post(REFRESH_URL, {'refresh': self.refresh_token}).data['refresh']
        response = self.client.post(REFRESH_URL, {'refresh': rotated})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_refresh_token_fails(self):
        response = self.client.post(REFRESH_URL, {'refresh': expired_token(RefreshToken, self.user)})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_refresh_token_fails(self):
        RefreshToken(self.refresh_token).blacklist()
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_cannot_be_used_as_refresh_token(self):
        response = self.client.post(REFRESH_URL, {'refresh': str(AccessToken.for_user(self.user))})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_for_inactive_user_fails(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        response = self.client.post(REFRESH_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_access_token_can_be_renewed(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token(AccessToken, self.user)}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials()
        new_access = self.client.post(REFRESH_URL, {'refresh': self.refresh_token}).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)


class ProtectedEndpointTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.user = create_user()

    def test_me_patch_unauthenticated_returns_401(self):
        self.assertEqual(self.client.patch(ME_URL, {'first_name': 'Pirate'}).status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_malformed_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer pas.un.jwt')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_as_bearer_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user)}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_access_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token(AccessToken, self.user)}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_signed_by_another_key_returns_401(self):
        forged = jwt.encode({**AccessToken.for_user(self.user).payload},
                            'cle-factice-qui-nest-pas-la-secret-key', algorithm='HS256')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {forged}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizationTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.alice = create_user(email='alice@example.com', username='alice')
        self.bob = create_user(email='bob@example.com', username='bob')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(self.bob)}')

    def test_me_returns_only_own_profile(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.data['email'], 'bob@example.com')
        self.assertNotIn('alice@example.com', str(response.data))

    def test_patch_cannot_target_another_user(self):
        self.client.patch(ME_URL, {'id': self.alice.id, 'username': 'pirate'})
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, 'alice')

    def test_patch_cannot_escalate_privileges(self):
        self.client.patch(ME_URL, {'is_staff': True, 'is_superuser': True})
        self.bob.refresh_from_db()
        self.assertFalse(self.bob.is_staff)
        self.assertFalse(self.bob.is_superuser)

    def test_token_of_deactivated_user_is_rejected(self):
        self.bob.is_active = False
        self.bob.save()
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutErrorTests(AuthAPITestCase):

    def setUp(self):
        super().setUp()
        self.user = create_user()
        login = self.client.post(LOGIN_URL, {'email': VALID_USER['email'], 'password': VALID_USER['password']})
        self.access_token = login.data['access']
        self.refresh_token = login.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def assert_invalid_token_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Token invalide.'})

    def test_logout_with_malformed_token(self):
        self.assert_invalid_token_response(self.client.post(LOGOUT_URL, {'refresh': 'invalid.token.here'}))

    def test_logout_with_already_blacklisted_token(self):
        self.client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.assert_invalid_token_response(self.client.post(LOGOUT_URL, {'refresh': self.refresh_token}))

    def test_logout_with_expired_refresh_token(self):
        response = self.client.post(LOGOUT_URL, {'refresh': expired_token(RefreshToken, self.user)})
        self.assert_invalid_token_response(response)

    def test_logout_with_access_token_instead_of_refresh(self):
        self.assert_invalid_token_response(self.client.post(LOGOUT_URL, {'refresh': self.access_token}))

    def test_server_failure_is_not_reported_as_invalid_token(self):
        client = APIClient(raise_request_exception=False)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        with mock.patch.object(RefreshToken, 'blacklist', side_effect=RuntimeError('panne base simulée')):
            with self.assertLogs('django.request', level='ERROR'):
                response = client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertNotIn('Token invalide', response.content.decode())

    def test_server_failure_log_contains_no_token_or_password(self):
        client = APIClient(raise_request_exception=False)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        with mock.patch.object(RefreshToken, 'blacklist', side_effect=RuntimeError('panne base simulée')):
            with self.assertLogs('django.request', level='ERROR') as captured:
                client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        formatter = logging.Formatter()
        logged = '\n'.join(
            record.getMessage() + (formatter.formatException(record.exc_info) if record.exc_info else '')
            for record in captured.records
        )
        self.assertIn('/api/v1/auth/logout/', logged)
        for sensitive in (self.access_token, self.refresh_token, VALID_USER['password']):
            self.assertNotIn(sensitive, logged)

    def test_access_token_remains_valid_until_expiry_after_logout(self):
        """Limite connue : la blacklist ne porte que sur les refresh tokens."""
        self.client.post(LOGOUT_URL, {'refresh': self.refresh_token})
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)
