from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import KeyResult, Diretoria
import logging
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Create your views here.

@require_GET
@login_required
def get_key_results(request):
    try:
        diretoria_id = request.GET.get('diretoria_id')
        logger.info(f'Recebida requisição para diretoria_id: {diretoria_id}')
        logger.info(f'Headers da requisição: {request.headers}')
        logger.info(f'Parâmetros GET: {request.GET}')

        if not diretoria_id:
            logger.warning('Nenhum diretoria_id fornecido')
            return JsonResponse({'error': 'diretoria_id é obrigatório'}, status=400)

        key_results = KeyResult.objects.filter(
            objetivo__time__diretoria_id=diretoria_id,
            ativo=True
        ).select_related(
            'objetivo',
            'objetivo__time',
            'objetivo__time__diretoria'
        )

        logger.info(f'Encontrados {key_results.count()} Key Results')
        
        data = [{
            'id': kr.id,
            'text': f"{kr.descricao} ({kr.objetivo.time.nome})"
        } for kr in key_results]

        logger.info(f'Dados preparados: {data}')
        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f'Erro ao processar requisição: {str(e)}', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
