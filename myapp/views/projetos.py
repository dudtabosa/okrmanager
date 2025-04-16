from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from okrs.models import Projeto, ProjetoProgresso
from django.db.models import Max
from collections import defaultdict
import logging

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
def projetos(request):
    """
    View para exibir a lista de projetos em formato de cards,
    agrupados por diretoria e ordenados por criticidade de status.
    """
    # Log para debug
    logger.warning("Renderizando página de projetos - " + str(request.path))
    
    # Obtém todos os projetos ativos
    projetos_ativos = Projeto.objects.filter(ativo=True)
    
    # Define a ordem de prioridade dos status
    ordem_status = {
        'CRITICO': 1,
        'ATRASADO': 2,
        'ATENCAO': 3,
        'EM_DIA': 4,
        'PAUSADO': 5,
        'CONCLUIDO': 6,
        'ENTREGUE': 7,
        'sem_status': 8
    }
    
    projetos_com_status = []
    for projeto in projetos_ativos:
        # Obtém o último progresso do projeto
        ultimo_progresso = ProjetoProgresso.objects.filter(
            projeto=projeto
        ).order_by('-data').first()
        
        if ultimo_progresso:
            projetos_com_status.append({
                'projeto': projeto,
                'progresso': ultimo_progresso,
                'status': ultimo_progresso.farol,
                'ultima_atualizacao': ultimo_progresso.data,
                'ordem_status': ordem_status.get(ultimo_progresso.farol, 9)
            })
        else:
            projetos_com_status.append({
                'projeto': projeto,
                'progresso': None,
                'status': 'sem_status',
                'ultima_atualizacao': None,
                'ordem_status': ordem_status.get('sem_status', 9)
            })
    
    # Ordena os projetos por criticidade (ordem_status)
    projetos_ordenados = sorted(projetos_com_status, key=lambda x: x['ordem_status'])
    
    # Agrupa os projetos por diretoria
    projetos_por_diretoria = defaultdict(list)
    for projeto in projetos_ordenados:
        diretoria_nome = projeto['projeto'].diretoria.nome
        projetos_por_diretoria[diretoria_nome].append(projeto)
    
    # Log para verificar estrutura
    logger.warning(f"Diretorias encontradas: {list(projetos_por_diretoria.keys())}")
    
    context = {
        'projetos': projetos_ordenados,  # Mantém a lista completa para compatibilidade
        'projetos_por_diretoria': dict(projetos_por_diretoria),  # Projetos agrupados por diretoria
        'cores_status': {
            'critico': 'purple',
            'atrasado': 'red',
            'no_prazo': 'green',
            'atencao': 'yellow',
            'pausado': 'gray',
            'concluido': 'blue',
            'entregue': 'blue',
            'sem_status': 'gray'
        },
        'page_title': 'Projetos',
        'menu_active': 'projetos'
    }
    
    return render(request, 'myapp/projetos.html', context) 