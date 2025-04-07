from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from okrs.models import Objetivo, Time

@login_required
def opah_okrs(request):
    try:
        # Obtém os times do usuário
        times = Time.objects.filter(usuarios=request.user)
        print(f"Times do usuário: {list(times)}")
        
        # Obtém os OKRs dos times do usuário
        okrs = Objetivo.objects.filter(time__in=times, ano=2025)
        print(f"OKRs encontrados: {len(okrs)}")
        
        # Calcula o progresso geral
        total_progresso = 0
        total_krs = 0
        
        for okr in okrs:
            print(f"Processando OKR: {okr.descricao}")
            okr_progresso = 0
            okr_total_krs = 0
            
            for kr in okr.key_results.all():
                print(f"KR: {kr.descricao}")
                print(f"Valor atual: {kr.valor_atual}, Target trimestral: {kr.valor_target}, Target anual: {kr.valor_target_anual}")
                
                # Calcula o progresso anual
                if kr.valor_target_anual > 0:
                    progresso_anual = (kr.valor_atual / kr.valor_target_anual) * 100
                    print(f"Progresso anual: {progresso_anual}")
                    
                    okr_progresso += progresso_anual
                    okr_total_krs += 1
            
            if okr_total_krs > 0:
                okr.progresso_geral = okr_progresso / okr_total_krs
                print(f"Progresso geral do OKR: {okr.progresso_geral} (okr_progresso: {okr_progresso}, okr_total_krs: {okr_total_krs})")
                
                total_progresso += okr.progresso_geral
                total_krs += 1
        
        progresso_geral = total_progresso / total_krs if total_krs > 0 else 0
        print(f"Progresso geral: {progresso_geral} (total_progresso: {total_progresso}, total_krs: {total_krs})")
        
        # Prepara o contexto para o template
        context = {
            'okrs': okrs,
            'progresso_geral': progresso_geral,
            'total_okrs': len(okrs),
            'total_times': len(times),
            'page_title': 'OKRs OPAH',
        }
        
        print(f"Contexto enviado para o template: {context}")
        
        # Renderiza o template
        response = render(request, 'myapp/opah_okrs.html', context)
        
        # Configura o cache
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Exception as e:
        print(f"Erro em opah_okrs: {str(e)}")
        return render(request, 'myapp/opah_okrs.html', {'error': str(e)}) 