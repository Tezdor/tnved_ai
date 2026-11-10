from ..models import ProductRequest
from .rate_limit import check_rate_limit, get_client_ip


GUEST_FREE_LIMIT = 2


def guest_limit_reached(request):
    return (
        not request.user.is_authenticated
        and request.session.get("guest_analysis_count", 0) >= GUEST_FREE_LIMIT
    )


def analysis_retry_after(request, *, scope, limit):
    if request.user.is_authenticated:
        identity = f"user:{request.user.pk}"
    else:
        identity = f"ip:{get_client_ip(request)}"

    return check_rate_limit(
        scope=scope,
        identity=identity,
        limit=limit,
        period_seconds=60,
    )


def available_product_requests(request):
    if request.user.is_authenticated:
        return ProductRequest.objects.filter(user=request.user)

    return ProductRequest.objects.filter(
        user__isnull=True,
        id__in=request.session.get("guest_request_ids", []),
    )