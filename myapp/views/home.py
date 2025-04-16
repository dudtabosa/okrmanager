from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from okrs.models import Time, Objetivo, KeyResult, KeyResultProgresso, TipoValor, Diretoria
from django.db.models import Avg, Count
from decimal import Decimal
import logging
from django.utils import timezone
from datetime import datetime

NUM_OF_ITEMS = 5
logger = logging.getLogger(__name__)

@login_required
def home(request):
    try:
        print("Iniciando home view")
        print(f"Usuário: {request.user}")
        
        # Obtém os times do usuário
        times_usuario = Time.objects.filter(membros=request.user, ativo=True)
        print(f"Times do usuário: {list(times_usuario)}")
        
        if not times_usuario.exists():
            print("Usuário não está em nenhum time ativo")
            return render(request, 'myapp/home.html', {
                'okrs': [],
                'progresso_geral': 0,
                'total_okrs': 0,
                'total_times': 0,
                'page_title': 'Meu Dashboard anual',
                'labels': ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre'],
                'dados_progresso': [0, 0, 0, 0],
            })
        
        # Obtém os OKRs dos times do usuário
        okrs = Objetivo.objects.filter(time__in=times_usuario, ativo=True).prefetch_related(
            'key_results',
            'time',
            'time__diretoria'
        ).order_by('-ano', 'time__nome')

        print(f"OKRs encontrados: {okrs.count()}")
        if okrs.exists():
            print(f"Primeiro OKR: {okrs.first().descricao}")
            print(f"Time do primeiro OKR: {okrs.first().time.nome}")
            print(f"KRs do primeiro OKR: {okrs.first().key_results.count()}")

        # Obtém todas as diretorias
        diretorias = Diretoria.objects.all()
        print(f"Total de diretorias: {diretorias.count()}")
        
        # Calcula a evolução trimestral usando o mesmo método do dashboard_geral
        evolucao_trimestral = [0, 0, 0, 0]
        for diretoria in diretorias:
            for t in range(1, 5):
                evolucao_trimestral[t-1] += diretoria.calcular_progresso_geral('2025', str(t))
        
        # Calcula a média da evolução trimestral
        if diretorias:
            evolucao_trimestral = [round(x / len(diretorias), 1) for x in evolucao_trimestral]
            print(f"Evolução trimestral: {evolucao_trimestral}")

        # Calcula o progresso geral como média dos trimestres
        progresso_geral = sum(evolucao_trimestral) / 4 if evolucao_trimestral else 0
        print(f"Progresso geral (média dos trimestres): {progresso_geral}")

        # Processa os OKRs para exibição
        for okr in okrs:
            print(f"\nProcessando OKR: {okr.descricao}")
            okr_progresso = 0
            okr_total_krs = 0
            
            for kr in okr.key_results.all():
                print(f"\nKR: {kr.descricao}")
                
                # Obtém o progresso mais recente
                ultimo_progresso = kr.progressos.order_by('-data_atualizacao').first()
                
                if ultimo_progresso:
                    valor_atual = Decimal(str(ultimo_progresso.valor_atual))
                    valor_target = Decimal(str(kr.valor_target))
                    
                    # Calcula o progresso baseado no tipo de valor
                    if kr.tipo_valor == TipoValor.PORCENTAGEM:
                        progresso_valor = valor_atual
                    else:
                        progresso_valor = (valor_atual / valor_target) * 100
                    
                    # Formata o valor atual baseado no tipo
                    if kr.tipo_valor == TipoValor.MOEDA:
                        kr.valor_formatado = f"R$ {valor_atual:,.2f}"
                    elif kr.tipo_valor == TipoValor.PORCENTAGEM:
                        kr.valor_formatado = f"{valor_atual:.1f}%"
                    else:
                        kr.valor_formatado = f"{valor_atual:.1f}"
                    
                    # Atualiza o progresso do KR
                    kr.progresso_atual = float(progresso_valor)
                    
                    # Define a cor do progresso
                    if progresso_valor >= 100:
                        kr.cor_progresso = 'bg-success'
                    elif progresso_valor >= 50:
                        kr.cor_progresso = 'bg-primary'
                    else:
                        kr.cor_progresso = 'bg-danger'
                    
                    # Acumula para o progresso do OKR
                    okr_progresso += float(progresso_valor)
                    okr_total_krs += 1
                else:
                    print(f"KR sem progresso: {kr.descricao}")
                    kr.progresso_atual = 0
                    kr.cor_progresso = 'bg-secondary'
                    okr_total_krs += 1
            
            # Calcula o progresso geral do OKR
            if okr_total_krs > 0:
                okr.progresso_geral = okr_progresso / okr_total_krs
                print(f"Progresso geral do OKR: {okr.progresso_geral}")
            else:
                okr.progresso_geral = 0
                print("OKR sem KRs com progresso")

        # Conta o total de KRs ativos
        total_krs_ativos = KeyResult.objects.filter(
            objetivo__time__in=times_usuario,
            objetivo__ativo=True,
            ativo=True
        ).count()
        print(f"Total de KRs ativos: {total_krs_ativos}")

        context = {
            'okrs': okrs,
            'progresso_geral': round(progresso_geral, 1),
            'total_okrs': total_krs_ativos,
            'total_times': times_usuario.count(),
            'page_title': 'Meu Dashboard anual',
            'labels': ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre'],
            'dados_progresso': evolucao_trimestral,
        }

        print(f"\nContexto enviado para o template: {context}")

        return render(request, 'myapp/home.html', context)
    except Exception as e:
        print(f"Erro em home: {str(e)}")
        return render(request, 'myapp/home.html', {'error': str(e)})

@login_required
def profile(request):
    context = {
        'user': request.user,
        'times': Time.objects.filter(membros=request.user, ativo=True)
    }
    return render(request, 'myapp/profile.html', context)
