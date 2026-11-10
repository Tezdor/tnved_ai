from unittest.mock import Mock, patch

import requests

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured

from api.core.turnstile import verify_turnstile

@override_settings(
    DEBUG=True,
    TURNSTILE_ENABLED=True,
    TURNSTILE_SITE_KEY="test-site-key",
    TURNSTILE_SECRET_KEY="test-secret-key"
)
class TurnstileServiceTests(SimpleTestCase):
    @patch("api.core.turnstile.requests.post")
    def test_success(self, post):
        post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"success": True})
        )

        self.assertTrue(verify_turnstile("test-token"))

    @patch("api.core.turnstile.requests.post")
    def test_invalid_responses(self, post):
        for result in (
            {"success": False},
            {"success": "true"},
            {},
            [],
        ):
            with self.subTest(result=result):
                post.return_value = Mock(
                    status_code=200,
                    json=Mock(return_value=result)
                )

                self.assertFalse(verify_turnstile("test-token"))

    @patch("api.core.turnstile.requests.post")
    def test_network_error(self, post):
        post.side_effect = requests.Timeout()

        self.assertFalse(verify_turnstile("test-token"))

    @patch("api.core.turnstile.requests.post")
    def test_http_error(self, post):
        post.return_value = Mock(status_code=503)

        self.assertFalse(verify_turnstile("test-token"))

    @patch("api.core.turnstile.requests.post")
    def test_invalid_json(self, post):
        post.return_value = Mock(
            status_code=200,
            json=Mock(side_effect=ValueError("Invalid JSON"))
        )

        self.assertFalse(verify_turnstile("test-token"))

    @patch("api.core.turnstile.requests.post")
    def test_missing_or_oversized_token(self, post):
        for token in ("", None, "x" * 2049):
            with self.subTest(token_length=len(token or "")):
                self.assertFalse(verify_turnstile(token))

        post.assert_not_called()

    @override_settings(TURNSTILE_ENABLED=False)
    @patch("api.core.turnstile.requests.post")
    def test_disabled(self, post):
        self.assertTrue(verify_turnstile(""))
        post.assert_not_called()

    @override_settings(
        DEBUG=False,
        TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA"
    )
    @patch("api.core.turnstile.requests.post")
    def test_production_rejects_test_keys(self, post):
        with self.assertRaises(ImproperlyConfigured):
            verify_turnstile("test-token")

        post.assert_not_called()
@override_settings(TRUST_NGINX_CLIENT_IP=False)
class TurnstileFormTests(TestCase):
    @patch("api.views.auth.check_rate_limit", return_value=0)
    @patch("api.views.auth.verify_turnstile", return_value=False)
    def test_registration_rejected(self, verify, rate_limit):
        response = self.client.post(
            "/api/register/",
            {
                "username": "blocked-user",
                "email": "blocked@example.com",
                "password1": "LongTestPassword-739!",
                "password2": "LongTestPassword-739!",
                "cf-turnstile-response": "rejected-token",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            User.objects.filter(username="blocked-user").exists()
        )
        verify.assert_called_once_with("rejected-token")

    @patch("api.views.auth.check_rate_limit", return_value=0)
    @patch("api.views.auth.verify_turnstile", return_value=False)
    def test_login_rejected(self, verify, rate_limit):
        User.objects.create_user(
            username="existing-user",
            password="LongTestPassword-739!"
        )

        response = self.client.post(
            "/api/login/",
            {
                "username": "existing-user",
                "password": "LongTestPassword-739!",
                "cf-turnstile-response": "rejected-token",
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)
        verify.assert_called_once_with("rejected-token")