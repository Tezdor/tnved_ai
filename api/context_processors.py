from django.conf import settings


def turnstile_settings(request):
    return {
        "turnstile_enabled": settings.TURNSTILE_ENABLED,
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
    }