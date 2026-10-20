from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'api/index.html')


@login_required(login_url='login')
def history_page(request):
    return render(request, 'api/history.html')