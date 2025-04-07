from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from okrs.models import Time, Objetivo, KeyResult, KeyResultProgresso, TipoValor
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
        
        # Obtém os times do usuário
        times_usuario = Time.objects.filter(membros=request.user, ativo=True)
        print(f"Times do usuário: {list(times_usuario)}")
        
        # Obtém os OKRs dos times do usuário
        okrs = Objetivo.objects.filter(time__in=times_usuario, ativo=True).prefetch_related(
            'key_results',
            'time',
            'time__diretoria'
        ).order_by('-ano', 'time__nome')

        print(f"OKRs encontrados: {okrs.count()}")

        # Inicializa variáveis para cálculos
        total_progresso = 0
        total_krs = 0
        
        # Inicializa variáveis para o gráfico
        medias_trimestrais = [0, 0, 0, 0]  # Médias para cada trimestre
        total_krs_por_trimestre = [0, 0, 0, 0]  # Total de KRs por trimestre

        # Adiciona os valores atuais dos Key Results aos objetos
        for okr in okrs:
            print(f"\nProcessando OKR: {okr.descricao}")
            okr_progresso = 0
            okr_total_krs = 0
            
            for kr in okr.key_results.all():
                print(f"\nKR: {kr.descricao}")
                
                # Calcula o progresso para cada trimestre (para o gráfico)
                for trimestre in range(1, 5):
                    # Obtém o progresso do trimestre
                    progresso = kr.progressos.filter(trimestre=str(trimestre)).order_by('-data_atualizacao').first()
                    
                    if progresso:
                        valor_atual = Decimal(str(progresso.valor_atual))
                        valor_target = Decimal(str(kr.valor_target))
                        
                        # Calcula o progresso baseado no tipo de valor
                        if kr.tipo_valor == TipoValor.PORCENTAGEM:
                            progresso_valor = valor_atual
                        else:
                            progresso_valor = (valor_atual / valor_target) * 100
                        
                        # Acumula para a média do trimestre
                        medias_trimestrais[trimestre-1] += float(progresso_valor)
                        total_krs_por_trimestre[trimestre-1] += 1
                
                # Obtém o progresso mais recente para o cálculo geral (anual)
                ultimo_progresso = kr.progressos.order_by('-data_atualizacao').first()
                
                if ultimo_progresso:
                    valor_atual = Decimal(str(ultimo_progresso.valor_atual))
                    valor_target_trimestral = Decimal(str(kr.valor_target))
                    valor_target_anual = valor_target_trimestral * 4  # Target anual é 4x o trimestral
                    
                    print(f"Valor atual: {valor_atual}, Target trimestral: {valor_target_trimestral}, Target anual: {valor_target_anual}")
                    
                    # Calcula o progresso baseado no tipo de valor
                    if kr.tipo_valor == TipoValor.PORCENTAGEM:
                        progresso = valor_atual
                    else:
                        progresso = (valor_atual / valor_target_anual) * 100
                    
                    print(f"Progresso anual: {progresso}")
                    
                    # Armazena o progresso no KR
                    kr.progresso_atual = float(progresso)
                    
                    # Acumula para o cálculo do progresso geral do OKR
                    okr_progresso += float(progresso)
                    okr_total_krs += 1
                    
                    # Acumula para o cálculo do progresso geral total
                    total_progresso += float(progresso)
                    total_krs += 1
                    
                    # Define a cor do progresso
                    if progresso < 50:
                        kr.cor_progresso = 'bg-danger'  # Vermelho para abaixo de 50%
                    elif progresso > 100:
                        kr.cor_progresso = 'bg-orange'  # Laranja para acima de 100%
                    else:
                        kr.cor_progresso = 'bg-primary'  # Azul para 100% ou abaixo
                else:
                    print(f"KR sem progresso: {kr.descricao}")
                    kr.progresso_atual = 0
                    kr.cor_progresso = 'bg-secondary'
                    okr_total_krs += 1
                    total_krs += 1
            
            # Calcula o progresso geral do OKR
            if okr_total_krs > 0:
                okr.progresso_geral = okr_progresso / okr_total_krs
                print(f"Progresso geral do OKR: {okr.progresso_geral} (okr_progresso: {okr_progresso}, okr_total_krs: {okr_total_krs})")
            else:
                okr.progresso_geral = 0
                print("OKR sem KRs com progresso")

        # Calcula o progresso geral
        progresso_geral = total_progresso / total_krs if total_krs > 0 else 0
        print(f"\nProgresso geral: {progresso_geral} (total_progresso: {total_progresso}, total_krs: {total_krs})")
        
        # Calcula as médias trimestrais
        for i in range(4):
            if total_krs_por_trimestre[i] > 0:
                medias_trimestrais[i] = medias_trimestrais[i] / total_krs_por_trimestre[i]
            else:
                medias_trimestrais[i] = 0
            print(f"Média do {i+1}º trimestre: {medias_trimestrais[i]}%")

        context = {
            'okrs': okrs,
            'progresso_geral': progresso_geral,
            'total_okrs': okrs.count(),
            'total_times': times_usuario.count(),
            'page_title': 'Meu Dashboard anual',
            'labels': ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre'],
            'dados_progresso': medias_trimestrais,
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
