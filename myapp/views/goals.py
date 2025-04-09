from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from okrs.models import Objetivo, KeyResultProgresso, Time, TipoValor, KeyResult, Diretoria
from decimal import Decimal
import logging
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)

def formata_valor_reais(valor):
    """Formata um valor decimal para o formato brasileiro de moeda"""
    try:
        valor_decimal = Decimal(str(valor))
        valor_formatado = '{:,.2f}'.format(valor_decimal).replace(',', '_').replace('.', ',').replace('_', '.')
        return f"R$ {valor_formatado}"
    except:
        return "R$ 0,00"

@login_required
def kr_history(request, kr_id):
    try:
        logger.info(f"Iniciando kr_history view para KR {kr_id}")
        
        # Obtém o KR específico
        kr = get_object_or_404(KeyResult, id=kr_id)
        logger.info(f"KR encontrado: {kr.descricao}")
        
        # Verifica se o usuário tem acesso ao KR
        if not Time.objects.filter(id=kr.objetivo.time.id, membros=request.user).exists():
            logger.warning(f"Usuário {request.user} não tem acesso ao KR {kr_id}")
            messages.error(request, 'Você não tem permissão para visualizar este KR.')
            return redirect('myapp:all_goals')

        # Obtém o histórico de progressos
        historico = kr.progressos.all().order_by('-data_atualizacao')
        
        # Calcula o progresso para cada registro do histórico
        for progresso in historico:
            valor_atual = Decimal(str(progresso.valor_atual))
            valor_target = Decimal(str(kr.valor_target))
            
            if kr.tipo_valor == TipoValor.PORCENTAGEM:
                progresso.progresso = float(valor_atual)
            else:
                progresso.progresso = float((valor_atual / valor_target) * 100)

        # Obtém o último valor e progresso
        ultimo_progresso = historico.first()
        if ultimo_progresso:
            ultimo_valor = ultimo_progresso.valor_atual
            if kr.tipo_valor == TipoValor.PORCENTAGEM:
                progresso_atual = float(ultimo_valor)
            else:
                progresso_atual = float((Decimal(str(ultimo_valor)) / Decimal(str(kr.valor_target))) * 100)
        else:
            ultimo_valor = 0
            progresso_atual = 0

        context = {
            'kr': kr,
            'historico': historico,
            'ultimo_valor': ultimo_valor,
            'progresso_atual': progresso_atual,
            'page_title': f'Histórico - {kr.descricao}',
        }

        logger.info("Renderizando template")
        return render(request, 'myapp/goals/kr_history.html', context)
    except Exception as e:
        logger.error(f"Erro em kr_history: {str(e)}", exc_info=True)
        messages.error(request, f'Erro ao carregar histórico: {str(e)}')
        return redirect('myapp:all_goals')

@login_required
def all_goals(request):
    try:
        logger.info("Iniciando all_goals view")
        
        # Obtém o mês atual
        mes_atual = datetime.now().month
        logger.info(f"Mês atual: {mes_atual}")
        
        # Calcula o trimestre atual baseado no mês
        if mes_atual in [1, 2, 3]:
            trimestre_atual = '1'
            logger.info("Trimestre 1: Janeiro, Fevereiro, Março")
        elif mes_atual in [4, 5, 6]:
            trimestre_atual = '2'
            logger.info("Trimestre 2: Abril, Maio, Junho")
        elif mes_atual in [7, 8, 9]:
            trimestre_atual = '3'
            logger.info("Trimestre 3: Julho, Agosto, Setembro")
        else:  # meses 10, 11, 12
            trimestre_atual = '4'
            logger.info("Trimestre 4: Outubro, Novembro, Dezembro")
            
        logger.info(f"Trimestre atual calculado: {trimestre_atual}")
        
        # Obtém o período selecionado
        periodo = request.GET.get('periodo')
        
        # Se não houver período selecionado (primeira vez), usa o trimestre atual
        if periodo is None:
            periodo = trimestre_atual
            logger.info(f"Primeiro acesso - usando trimestre atual: {periodo}")
        else:
            logger.info(f"Período selecionado pelo usuário: {periodo}")
        
        # Obtém os times do usuário através do modelo Time
        times_usuario = Time.objects.filter(membros=request.user, ativo=True)
        logger.info(f"Times do usuário: {list(times_usuario)}")
        
        # Obtém os OKRs dos times do usuário
        okrs = Objetivo.objects.filter(time__in=times_usuario, ativo=True).prefetch_related(
            'key_results',
            'time',
            'time__diretoria'
        ).order_by('-ano', 'time__nome')

        logger.info(f"OKRs encontrados: {okrs.count()}")

        # Variáveis para cálculo da média geral
        total_progresso_geral = 0
        total_krs_geral = 0

        # Adiciona os valores atuais dos Key Results aos objetos
        for okr in okrs:
            total_progresso = 0
            total_krs = 0
            
            # Itera sobre todos os KRs
            for kr in okr.key_results.all():
                # Filtra o progresso baseado no período selecionado
                if periodo == 'ano':
                    # Para o ano todo, pega o último progresso
                    ultimo_progresso = kr.progressos.order_by('-data_atualizacao').first()
                else:
                    # Para trimestres específicos, pega o progresso do trimestre
                    ultimo_progresso = kr.progressos.filter(trimestre=periodo).order_by('-data_atualizacao').first()
                
                if ultimo_progresso:
                    valor_atual = Decimal(str(ultimo_progresso.valor_atual))
                    valor_target = Decimal(str(kr.valor_target))
                    
                    # Calcula o progresso baseado no tipo de valor
                    if kr.tipo_valor == TipoValor.PORCENTAGEM:
                        # Para porcentagem, usa o valor diretamente
                        progresso = valor_atual
                    else:
                        # Para outros tipos, calcula a porcentagem em relação ao target
                        progresso = (valor_atual / valor_target) * 100
                    
                    # Formata o valor atual baseado no tipo
                    if kr.tipo_valor == TipoValor.MOEDA:
                        kr.valor_formatado = formata_valor_reais(valor_atual)
                        logger.info(f"Formatando valor em reais: {valor_atual} -> {kr.valor_formatado}")
                    elif kr.tipo_valor == TipoValor.PORCENTAGEM:
                        kr.valor_formatado = f"{valor_atual:.1f}%"
                    else:
                        kr.valor_formatado = f"{valor_atual:.1f}"
                else:
                    # Se não houver progresso, considera 0%
                    progresso = 0
                    if kr.tipo_valor == TipoValor.MOEDA:
                        kr.valor_formatado = "R$ 0,00"
                    elif kr.tipo_valor == TipoValor.PORCENTAGEM:
                        kr.valor_formatado = "0,0%"
                    else:
                        kr.valor_formatado = "0,0"
                
                # Define a cor do progresso
                if progresso < 50:
                    kr.cor_progresso = 'bg-danger'  # Vermelho para menos de 50%
                elif progresso > 100:
                    kr.cor_progresso = 'bg-warning'  # Laranja para mais de 100%
                else:
                    kr.cor_progresso = 'bg-primary'  # Azul para entre 50% e 100%
                
                # Armazena o progresso sem limitar a 100%
                kr.progresso_atual = float(progresso)
                
                # Acumula para o cálculo do progresso geral
                total_progresso += float(progresso)
                total_krs += 1
                
                # Acumula para o cálculo da média geral
                total_progresso_geral += float(progresso)
                total_krs_geral += 1
            
            # Calcula o progresso geral do objetivo
            okr.progresso_geral = total_progresso / total_krs if total_krs > 0 else 0

        # Calcula a média geral de todos os KRs
        media_geral = total_progresso_geral / total_krs_geral if total_krs_geral > 0 else 0
        logger.info(f"Média geral dos KRs: {media_geral:.1f}%")

        context = {
            'okrs': okrs,
            'page_title': f'OKRs do {periodo}º Trimestre: {media_geral:.1f}%',
            'periodo': periodo,
            'trimestre_atual': trimestre_atual,
            'media_geral': media_geral,
        }

        logger.info("Renderizando template")
        return render(request, 'myapp/goals/list.html', context)
    except Exception as e:
        logger.error(f"Erro em all_goals: {str(e)}", exc_info=True)
        messages.error(request, f'Erro ao carregar OKRs: {str(e)}')
        return redirect('myapp:home')

@login_required
def add_result(request, okr_id):
    try:
        logger.info(f"Iniciando add_result view para OKR {okr_id}")
        
        # Obtém o OKR específico
        okr = get_object_or_404(Objetivo, id=okr_id)
        logger.info(f"OKR encontrado: {okr.descricao}")
        
        # Verifica se o usuário tem acesso ao OKR
        if not Time.objects.filter(id=okr.time.id, membros=request.user).exists():
            logger.warning(f"Usuário {request.user} não tem acesso ao OKR {okr_id}")
            messages.error(request, 'Você não tem permissão para adicionar resultados a este OKR.')
            return redirect('myapp:all_goals')

        if request.method == 'POST':
            logger.info("Processando formulário POST")
            try:
                # Determina o trimestre atual
                mes_atual = datetime.now().month
                trimestre = str((mes_atual - 1) // 3 + 1)
                
                # Processa cada KR do OKR
                for kr in okr.key_results.all():
                    valor_atual = request.POST.get(f'valor_atual_{kr.id}')
                    if valor_atual:
                        # Cria um novo progresso
                        KeyResultProgresso.objects.create(
                            key_result=kr,
                            trimestre=trimestre,
                            valor_atual=valor_atual,
                            atualizado_por=request.user
                        )
                        logger.info(f"Progresso salvo para KR {kr.id}: {valor_atual}")

                messages.success(request, 'Resultados salvos com sucesso!')
                return redirect('myapp:all_goals')
            except Exception as e:
                logger.error(f"Erro ao salvar resultados: {str(e)}", exc_info=True)
                messages.error(request, f'Erro ao salvar resultados: {str(e)}')
                return redirect('myapp:add_result', okr_id=okr_id)

        context = {
            'okr': okr,
            'page_title': f'Adicionar Resultado - {okr.descricao}',
        }

        logger.info("Renderizando template de adição de resultado")
        return render(request, 'myapp/goals/add_result.html', context)
    except Exception as e:
        logger.error(f"Erro em add_result: {str(e)}", exc_info=True)
        messages.error(request, f'Erro ao carregar formulário: {str(e)}')
        return redirect('myapp:all_goals')

def dashboard_geral(request):
    # Ano fixo em 2025
    ano = '2025'
    
    # Obter o trimestre selecionado
    trimestre = request.GET.get('trimestre', 'ano')
    
    # Obter todas as diretorias
    diretorias = Diretoria.objects.all()
    
    # Preparar dados para os gráficos
    diretorias_nomes = []
    diretorias_progresso = []
    evolucao_trimestral = [0, 0, 0, 0]
    
    for diretoria in diretorias:
        # Progresso por diretoria
        diretorias_nomes.append(diretoria.nome)
        
        # Calcula o progresso da diretoria
        if trimestre == 'ano':
            # Para o ano todo, calcula a média dos 4 trimestres
            progresso_trimestres = []
            for t in range(1, 5):
                progresso = diretoria.calcular_progresso_geral(ano, str(t))
                progresso_trimestres.append(progresso)
                evolucao_trimestral[t-1] += progresso
            diretoria.progresso_atual = sum(progresso_trimestres) / len(progresso_trimestres)
        else:
            # Para trimestres específicos
            diretoria.progresso_atual = diretoria.calcular_progresso_geral(ano, trimestre)
            for t in range(1, 5):
                evolucao_trimestral[t-1] += diretoria.calcular_progresso_geral(ano, str(t))
        
        diretorias_progresso.append(diretoria.progresso_atual)
        
        # Dados dos times por diretoria
        times = Time.objects.filter(diretoria=diretoria)
        diretoria.times_nomes = [time.nome for time in times]
        
        # Calcula o progresso dos times
        diretoria.times_progresso = []
        for time in times:
            # Obtém todos os KRs ativos do time
            krs = KeyResult.objects.filter(
                objetivo__time=time,
                objetivo__ano=ano,
                objetivo__ativo=True,
                ativo=True
            ).prefetch_related('progressos')
            
            total_progresso = 0
            total_krs = 0
            
            for kr in krs:
                if trimestre == 'ano':
                    # Para o ano todo, calcula a média dos 4 trimestres
                    progresso_trimestres = []
                    for t in range(1, 5):
                        progresso = kr.progressos.filter(trimestre=str(t)).order_by('-data_atualizacao').first()
                        if progresso:
                            valor_atual = Decimal(str(progresso.valor_atual))
                            valor_target = Decimal(str(kr.valor_target))
                            
                            if kr.tipo_valor == TipoValor.PORCENTAGEM:
                                progresso_kr = float(valor_atual)
                            else:
                                progresso_kr = float((valor_atual / valor_target) * 100)
                        else:
                            progresso_kr = 0
                        progresso_trimestres.append(progresso_kr)
                    
                    # Calcula a média dos trimestres
                    progresso_kr = sum(progresso_trimestres) / len(progresso_trimestres)
                else:
                    # Para trimestres específicos, pega o progresso do trimestre
                    progresso = kr.progressos.filter(trimestre=trimestre).order_by('-data_atualizacao').first()
                    if progresso:
                        valor_atual = Decimal(str(progresso.valor_atual))
                        valor_target = Decimal(str(kr.valor_target))
                        
                        if kr.tipo_valor == TipoValor.PORCENTAGEM:
                            progresso_kr = float(valor_atual)
                        else:
                            progresso_kr = float((valor_atual / valor_target) * 100)
                    else:
                        progresso_kr = 0
                
                total_progresso += progresso_kr
                total_krs += 1
            
            time_progresso = round(total_progresso / total_krs, 1) if total_krs > 0 else 0
            diretoria.times_progresso.append(time_progresso)
        
        # Conta o total de KRs ativos da diretoria
        diretoria.total_okrs = KeyResult.objects.filter(
            objetivo__time__diretoria=diretoria,
            objetivo__ano=ano,
            objetivo__ativo=True,
            ativo=True
        ).count()
    
    # Calcular média da evolução trimestral
    if diretorias:
        evolucao_trimestral = [round(x / len(diretorias), 1) for x in evolucao_trimestral]
    
    context = {
        'diretorias': diretorias,
        'diretorias_nomes': diretorias_nomes,
        'diretorias_progresso': diretorias_progresso,
        'evolucao_trimestral': evolucao_trimestral,
        'ano': ano,
        'trimestre': trimestre,
        'page_title': 'Dashboard Geral'
    }
    
    return render(request, 'myapp/dashboard_geral.html', context) 