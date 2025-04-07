from django.core.management.base import BaseCommand
from okrs.models import KeyResultProgresso
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Atualiza todos os registros de progresso dos KRs para o 1º trimestre de 2025'

    def handle(self, *args, **options):
        try:
            # Data alvo: 31/03/2025 12:00
            data_alvo = datetime(2025, 3, 31, 12, 0, 0, tzinfo=timezone.get_current_timezone())
            
            # Atualiza todos os registros
            registros_atualizados = KeyResultProgresso.objects.all().update(
                trimestre='1',
                data_atualizacao=data_alvo
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Sucesso! {registros_atualizados} registros foram atualizados.')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao atualizar registros: {str(e)}')
            ) 