from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST

from ..forms import RegisterForm
from ..models import ProductRequest

from ..core.rate_limit import check_rate_limit, get_client_ip
from ..core.turnstile import verify_turnstile

def login_with_pending_analysis(request, user):
    pending_id = request.session.pop("pending_guest_request_id", None)
    guest_request_ids = request.session.get("guest_request_ids", [])

    login(request, user)

    if type(pending_id) is int and pending_id in guest_request_ids:
        ProductRequest.objects.filter(
            pk=pending_id,
            user__isnull=True,
            analysis_in_progress=False,
            final__isnull=True,
        ).update(user=user)

def register_view(request):
    if request.method == 'POST':
        retry_after = check_rate_limit(
            scope="register",
            identity=get_client_ip(request),
            limit=3,
            period_seconds=3600
        )

        if retry_after:
            response = render(
                request,
                'api/register.html',
                {
                    'form': RegisterForm(),
                    'retry_after': retry_after,
                    'rate_limit_error': (
                        "Слишком много попыток регистрации. "
                        f"Повторите через {(retry_after + 59) // 60} мин."
                    ),
                },
                status=429
            )
            response["Retry-After"] = str(retry_after)
            response["Cache-Control"] = "no-store"
            return response

        if not verify_turnstile(
            request.POST.get("cf-turnstile-response", "")
        ):
            return render(
                request,
                'api/register.html',
                {
                    'form': RegisterForm(),
                    'turnstile_error': (
                        "Проверка не пройдена. "
                        "Пройдите проверку ещё раз и повторите отправку."
                    ),
                },
                status=400
            )
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login_with_pending_analysis(request, user)
            return redirect('index')
    else:
        form = RegisterForm()

    return render(
        request,
        'api/register.html',
        {'form': form}
    )


def login_view(request):
    if request.method == 'POST':
        retry_after = check_rate_limit(
            scope="login",
            identity=get_client_ip(request),
            limit=5,
            period_seconds=60
        )

        if retry_after:
            response = render(
                request,
                'api/login.html',
                {
                    'form': AuthenticationForm(request),
                    'retry_after': retry_after,
                    'rate_limit_error': (
                        "Слишком много попыток входа. "
                        f"Повторите через {retry_after} сек."
                    ),
                },
                status=429
            )
            response["Retry-After"] = str(retry_after)
            response["Cache-Control"] = "no-store"
            return response

        if not verify_turnstile(
            request.POST.get("cf-turnstile-response", "")
        ):
            return render(
                request,
                'api/login.html',
                {
                    'form': AuthenticationForm(request),
                    'turnstile_error': (
                        "Проверка не пройдена. "
                        "Пройдите проверку ещё раз и повторите отправку."
                    ),
                },
                status=400
            )
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login_with_pending_analysis(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        'api/login.html',
        {'form': form}
    )

@require_POST
def logout_view(request):
    logout(request)
    return redirect('index')