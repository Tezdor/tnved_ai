from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import ProductRequest


@login_required(login_url='login')
def account_page(request):
    completed_count = ProductRequest.objects.filter(
        user=request.user,
        final__isnull=False
    ).count()

    return render(
        request,
        'api/account.html',
        {
            'completed_count': completed_count,
        }
    )