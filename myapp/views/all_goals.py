from django.contrib.auth.decorators import login_required
from okrs.models import Time, Objetivo, KeyResult, KeyResultProgresso, TipoValor
from decimal import Decimal
from datetime import datetime
import sys

@login_required
def all_goals(request):
    try:
        # Print direto para stdout
        sys.stdout.write("\n=== TESTE DE LOG ===\n")
        sys.stdout.flush()
        
        print("TESTE DE PRINT SIMPLES")
        
        # Obtém o mês atual
        mes_atual = datetime.now().month
        print(f"Mês atual: {mes_atual}")
        
        # Calcula o trimestre atual baseado no mês
        if mes_atual in [1, 2, 3]:
            trimestre_atual = '1'
            print("Trimestre 1: Janeiro, Fevereiro, Março")
        elif mes_atual in [4, 5, 6]:
            trimestre_atual = '2'
            print("Trimestre 2: Abril, Maio, Junho")
        elif mes_atual in [7, 8, 9]:
            trimestre_atual = '3'
            print("Trimestre 3: Julho, Agosto, Setembro")
        else:  # meses 10, 11, 12
            trimestre_atual = '4'
            print("Trimestre 4: Outubro, Novembro, Dezembro")
            
        print(f"Trimestre atual calculado: {trimestre_atual}")
        
        # Obtém os times do usuário
        times_usuario = Time.objects.filter(membros=request.user, ativo=True)
        print(f"Times do usuário: {list(times_usuario)}")
        
        # Obtém o período selecionado, usando o trimestre atual como padrão
        periodo = request.GET.get('periodo', trimestre_atual)
        print(f"Período selecionado: {periodo}")
        
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

        # Adiciona os valores atuais dos Key Results aos objetos
        for okr in okrs:
            print(f"Processando OKR: {okr.descricao}")
            okr_progresso = 0
            okr_total_krs = 0
            
            for kr in okr.key_results.all():
                print(f"KR: {kr.descricao}")
                # Obtém o progresso mais recente
                progresso = kr.progressos.order_by('-data_atualizacao').first()
                
                if progresso:
                    valor_atual = Decimal(str(progresso.valor_atual))
                    valor_target = Decimal(str(kr.valor_target))
                    
                    print(f"Valor atual: {valor_atual}")
                    print(f"Target: {valor_target}")
                    
                    # Calcula o progresso baseado no tipo de valor
                    if kr.tipo_valor == TipoValor.PORCENTAGEM:
                        progresso = valor_atual
                        print(f"Progresso (porcentagem): {progresso}")
                    else:
                        progresso = (valor_atual / valor_target) * 100
                        print(f"Progresso (valor absoluto): {progresso}")
                    
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
        print(f"Progresso geral: {progresso_geral} (total_progresso: {total_progresso}, total_krs: {total_krs})")

        context = {
            'okrs': okrs,
            'progresso_geral': progresso_geral,
            'total_okrs': okrs.count(),
            'total_times': times_usuario.count(),
            'periodo': periodo,
            'trimestre_atual': trimestre_atual,
            'page_title': 'Todos os OKRs',
        }

        print(f"Contexto enviado para o template: {context}")

        response = render(request, 'myapp/all_goals.html', context)
        
        # Adiciona headers para evitar cache
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Exception as e:
        print(f"Erro em all_goals: {str(e)}")
        return render(request, 'myapp/all_goals.html', {'error': str(e)}) 