import math

from ipaddress import ip_address
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.conf import settings
from django.core.exceptions import SuspiciousOperation

from ..models import RateLimitBucket


def check_rate_limit(*, scope, identity, limit, period_seconds):
    """
    Возвращает 0, если запрос разрешён.
    Иначе — число секунд до следующей разрешённой попытки.
    """
    if limit < 1 or period_seconds < 1:
        raise ValueError("Лимит и период должны быть положительными.")

    key = salted_hmac(
        key_salt=f"tnved.rate_limit.{scope}",
        value=str(identity),
        algorithm="sha256"
    ).hexdigest()

    with transaction.atomic():
        bucket, _ = (
            RateLimitBucket.objects
            .select_for_update()
            .get_or_create(
                key=key,
                defaults={
                    "window_started_at": timezone.now(),
                    "request_count": 0,
                }
            )
        )

        now = timezone.now()
        window_end = bucket.window_started_at + timedelta(
            seconds=period_seconds
        )

        if now >= window_end:
            bucket.window_started_at = now
            bucket.request_count = 0
            window_end = now + timedelta(seconds=period_seconds)

        if bucket.request_count >= limit:
            return max(
                1,
                math.ceil((window_end - now).total_seconds())
            )

        bucket.request_count += 1
        bucket.save(
            update_fields=[
                "window_started_at",
                "request_count",
            ]
        )

    return 0

def get_client_ip(request):
    if settings.TRUST_NGINX_CLIENT_IP:
        address = request.META.get("HTTP_X_REAL_IP")
    else:
        address = request.META.get("REMOTE_ADDR")

    try:
        return str(ip_address(address))
    except (ValueError, TypeError):
        raise SuspiciousOperation("Не удалось определить IP клиента.")