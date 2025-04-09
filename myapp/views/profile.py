from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    context = {
        'page_title': 'Meu Perfil',
        'user': request.user
    }
    return render(request, 'myapp/profile.html', context) 