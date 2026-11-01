import requests

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


TEST_KEYS = {
    "1x00000000000000000000AA",
    "2x00000000000000000000AB",
    "1x00000000000000000000BB",
    "2x00000000000000000000BB",
    "3x00000000000000000000FF",
    "1x0000000000000000000000000000000AA",
    "2x0000000000000000000000000000000AA",
    "3x0000000000000000000000000000000AA",
}


def verify_turnstile(token):
    if not settings.TURNSTILE_ENABLED:
        return True

    if not settings.TURNSTILE_SITE_KEY or not settings.TURNSTILE_SECRET_KEY:
        raise ImproperlyConfigured(
            "Turnstile включён, но ключи не настроены."
        )

    if not settings.DEBUG and (
        settings.TURNSTILE_SITE_KEY in TEST_KEYS
        or settings.TURNSTILE_SECRET_KEY in TEST_KEYS
    ):
        raise ImproperlyConfigured(
            "Тестовые ключи Turnstile запрещены при DEBUG=False."
        )

    if not isinstance(token, str):
        return False

    token = token.strip()

    if not token or len(token) > 2048:
        return False

    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.TURNSTILE_SECRET_KEY,
                "response": token,
            },
            timeout=(3, 8),
            allow_redirects=False
        )

        if response.status_code != 200:
            return False

        result = response.json()

    except (requests.RequestException, ValueError):
        return False

    return (
        isinstance(result, dict)
        and result.get("success") is True
    )