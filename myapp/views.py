from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from okrs.models import Time, Objetivo, KeyResult, KeyResultProgresso
from django.db.models import Avg, Count

@login_required
def home(request):
    # Obtém os times do usuário
    times_usuario = Time.objects.filter(membros=request.user, ativo=True)
    
    # Obtém os OKRs dos times do usuário
    okrs = Objetivo.objects.filter(time__in=times_usuario, ativo=True).prefetch_related(
        'key_results',
        'time',
        'time__diretoria'
    ).order_by('-ano', 'time__nome')

    # Calcula o progresso geral dos OKRs
    progresso_geral = KeyResultProgresso.objects.filter(
        key_result__objetivo__in=okrs
    ).aggregate(
        avg_progress=Avg('valor_atual')
    )['avg_progress'] or 0

    # Dados para o gráfico de progresso
    progressos_por_trimestre = KeyResultProgresso.objects.filter(
        key_result__objetivo__in=okrs
    ).values('trimestre').annotate(
        progresso_medio=Avg('valor_atual')
    ).order_by('trimestre')

    labels = [f"{trim}º Trimestre" for trim in range(1, 5)]
    dados_progresso = []
    
    # Organiza os dados do gráfico
    for trimestre in range(1, 5):
        progresso = next(
            (p['progresso_medio'] for p in progressos_por_trimestre if p['trimestre'] == str(trimestre)),
            0
        )
        dados_progresso.append(float(progresso))

    context = {
        'okrs': okrs,
        'progresso_geral': round(float(progresso_geral), 1),
        'total_okrs': okrs.count(),
        'total_times': times_usuario.count(),
        'labels': labels,
        'dados_progresso': dados_progresso,
    }

    return render(request, 'myapp/home.html', context)

@login_required
def profile(request):
    context = {
        'user': request.user,
        'times': Time.objects.filter(membros=request.user, ativo=True)
    }
    return render(request, 'myapp/profile.html', context) 