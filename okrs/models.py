from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import logging
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.

logger = logging.getLogger(__name__)

class TipoValor(models.TextChoices):
    INTEIRO = 'INT', 'Número Inteiro'
    PORCENTAGEM = 'PORC', 'Porcentagem'
    MOEDA = 'MOEDA', 'Valor em Reais'

class Diretoria(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome da Diretoria')
    descricao = models.TextField(verbose_name='Descrição', blank=True, null=True)
    membros = models.ManyToManyField(User, related_name='diretorias', verbose_name='Membros')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Diretoria'
        verbose_name_plural = 'Diretorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def calcular_progresso_geral(self, ano=None, trimestre=None):
        """
        Calcula o progresso geral da diretoria para um ano e trimestre específicos.
        Se não for especificado um trimestre, calcula para o ano todo.
        """
        if not ano:
            return 0
        
        times = self.times.all()
        total_progresso = 0
        total_okrs = 0
        
        for time in times:
            okrs = time.objetivos.filter(ano=ano)
            for okr in okrs:
                krs = okr.key_results.filter(ativo=True)
                if krs.exists():
                    for kr in krs:
                        # Obtém o progresso do trimestre específico
                        if trimestre:
                            progresso = kr.progressos.filter(trimestre=trimestre).order_by('-data_atualizacao').first()
                        else:
                            progresso = kr.progressos.order_by('-data_atualizacao').first()
                        
                        if progresso:
                            valor_atual = Decimal(str(progresso.valor_atual))
                            valor_target = Decimal(str(kr.valor_target))
                            
                            if kr.tipo_valor == TipoValor.PORCENTAGEM:
                                progresso_kr = float(valor_atual)
                            else:
                                progresso_kr = float((valor_atual / valor_target) * 100)
                            
                            total_progresso += progresso_kr
                            total_okrs += 1
        
        if total_okrs > 0:
            return total_progresso / total_okrs
        return 0

class Time(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome do Time')
    descricao = models.TextField(verbose_name='Descrição', blank=True, null=True)
    diretoria = models.ForeignKey(Diretoria, on_delete=models.CASCADE, related_name='times', verbose_name='Diretoria')
    membros = models.ManyToManyField(User, related_name='times', verbose_name='Membros', blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Time'
        verbose_name_plural = 'Times'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.diretoria.nome}"

    def calcular_progresso_geral(self, ano, trimestre):
        """Calcula o progresso geral do time para um ano e trimestre específicos"""
        try:
            # Obtém todos os OKRs ativos do time no ano especificado
            okrs = Objetivo.objects.filter(
                time=self,
                ano=ano,
                ativo=True
            ).prefetch_related('key_results', 'key_results__progressos')

            if not okrs.exists():
                return 0

            total_progresso = 0
            total_krs = 0

            # Calcula o progresso de cada OKR
            for okr in okrs:
                # Filtra apenas os KRs ativos
                for kr in okr.key_results.filter(ativo=True):
                    # Filtra o progresso baseado no trimestre
                    progresso = kr.progressos.filter(trimestre=trimestre).order_by('-data_atualizacao').first()
                    
                    if progresso:
                        valor_atual = Decimal(str(progresso.valor_atual))
                        valor_target = Decimal(str(kr.valor_target))
                        
                        if kr.tipo_valor == TipoValor.PORCENTAGEM:
                            # Para porcentagem, usa o valor diretamente
                            progresso_kr = float(valor_atual)
                        else:
                            # Para outros tipos, calcula a porcentagem em relação ao target
                            progresso_kr = float((valor_atual / valor_target) * 100)
                    else:
                        # Se não houver progresso, considera 0%
                        progresso_kr = 0

                    total_progresso += progresso_kr
                    total_krs += 1

            # Calcula a média geral
            return round(total_progresso / total_krs, 1) if total_krs > 0 else 0
        except Exception as e:
            logger.error(f"Erro ao calcular progresso geral do time {self.id}: {str(e)}")
            return 0

class Objetivo(models.Model):
    time = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='objetivos', verbose_name='Time')
    descricao = models.TextField(verbose_name='Descrição do Objetivo')
    ano = models.IntegerField(verbose_name='Ano')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'
        ordering = ['-ano', 'time']

    def __str__(self):
        return f"{self.descricao[:50]}... - {self.time.nome} ({self.ano})"

class KeyResult(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE, related_name='key_results', verbose_name='Objetivo')
    descricao = models.TextField(verbose_name='Descrição do Key Result')
    tipo_valor = models.CharField(
        max_length=5,
        choices=TipoValor.choices,
        default=TipoValor.INTEIRO,
        verbose_name='Tipo de Valor'
    )
    valor_target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Valor Target',
        help_text='Valor alvo a ser atingido'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Key Result'
        verbose_name_plural = 'Key Results'
        ordering = ['objetivo', 'descricao']

    def __str__(self):
        return f"{self.descricao[:50]}... - {self.objetivo.time.nome}"

class KeyResultProgresso(models.Model):
    TRIMESTRES = [
        ('1', '1º Trimestre'),
        ('2', '2º Trimestre'),
        ('3', '3º Trimestre'),
        ('4', '4º Trimestre'),
    ]
    
    key_result = models.ForeignKey(KeyResult, on_delete=models.CASCADE, related_name='progressos', verbose_name='Key Result')
    diretoria = models.ForeignKey(Diretoria, on_delete=models.CASCADE, verbose_name='Diretoria', null=True, blank=True)
    data_progresso = models.DateField(
        verbose_name='Data do Progresso',
        help_text='Data em que o progresso foi registrado',
        default=timezone.now
    )
    trimestre = models.CharField(max_length=1, choices=TRIMESTRES, verbose_name='Trimestre')
    valor_atual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Valor Atual',
        help_text='Valor atual do progresso'
    )
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Atualizado por')

    class Meta:
        verbose_name = 'Progresso do Key Result'
        verbose_name_plural = 'Progressos dos Key Results'
        ordering = ['key_result', 'trimestre']
        unique_together = ['key_result', 'trimestre']

    def __str__(self):
        return f"{self.key_result.descricao[:30]}... - {self.trimestre}º Trimestre"
        
    def save(self, *args, **kwargs):
        if self.key_result and not self.diretoria:
            self.diretoria = self.key_result.objetivo.time.diretoria
        
        # Calcula o trimestre baseado na data do progresso apenas para novos registros
        if not self.pk and self.data_progresso:
            mes = self.data_progresso.month
            if mes <= 3:
                self.trimestre = '1'
            elif mes <= 6:
                self.trimestre = '2'
            elif mes <= 9:
                self.trimestre = '3'
            else:
                self.trimestre = '4'
        
        super().save(*args, **kwargs)

class KPI(models.Model):
    RELEVANCIA_CHOICES = [
        ('ALTA', 'Alta'),
        ('MEDIA', 'Média'),
        ('BAIXA', 'Baixa')
    ]

    nome = models.CharField(max_length=200, verbose_name='Nome do KPI')
    descricao = models.TextField(verbose_name='Descrição')
    formula_calculo = models.TextField(
        verbose_name='Fórmula de Cálculo',
        help_text='Descreva a fórmula ou método de cálculo deste KPI'
    )
    relevancia = models.CharField(
        max_length=5,
        choices=RELEVANCIA_CHOICES,
        default='MEDIA',
        verbose_name='Relevância'
    )
    tipo_valor = models.CharField(
        max_length=20,
        choices=[
            ('NUMERO', 'Número'),
            ('PORCENTAGEM', 'Porcentagem'),
            ('MOEDA', 'Moeda')
        ],
        default='NUMERO',
        verbose_name='Tipo de Valor'
    )
    valor_target = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Valor Target'
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        ordering = ['-relevancia', 'nome']

    def __str__(self):
        return f"{self.nome} - Relevância: {self.get_relevancia_display()}"

class KPIProgresso(models.Model):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='progressos')
    valor_atual = models.DecimalField(max_digits=10, decimal_places=2)
    data_medicao = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Progresso do KPI'
        verbose_name_plural = 'Progressos dos KPIs'
        ordering = ['-data_medicao']

    def __str__(self):
        return f"{self.kpi.nome} - {self.data_medicao}"

class Projeto(models.Model):
    nome = models.CharField(max_length=200, verbose_name='Nome do Projeto')
    descricao = models.TextField(verbose_name='Descrição')
    cliente = models.CharField(max_length=200, verbose_name='Cliente', blank=True, null=True)
    diretoria = models.ForeignKey(Diretoria, on_delete=models.CASCADE, related_name='projetos', verbose_name='Diretoria Responsável')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    custo_planejado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Custo Planejado',
        help_text='Custo total planejado para o projeto'
    )
    receita_planejada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Receita Planejada',
        help_text='Receita total planejada para o projeto'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.nome} - {self.diretoria.nome}"

class ProjetoProgresso(models.Model):
    FAROL_CHOICES = [
        ('CRITICO', 'Crítico'),
        ('ATRASADO', 'Atrasado'),
        ('EM_DIA', 'Em Dia'),
        ('ATENCAO', 'Atenção'),
        ('PAUSADO', 'Pausado'),
        ('CONCLUIDO', 'Concluído'),
        ('ENTREGUE', 'Entregue')
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='progressos', verbose_name='Projeto', null=False, blank=False)
    diretoria = models.ForeignKey(Diretoria, on_delete=models.CASCADE, verbose_name='Diretoria')
    data = models.DateField(verbose_name='Data do Progresso', default=timezone.now)
    custo_realizado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Custo Realizado',
        help_text='Custo realizado até a data'
    )
    receita_realizada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Receita Realizada',
        help_text='Receita realizada até a data'
    )
    farol = models.CharField(
        max_length=10,
        choices=FAROL_CHOICES,
        verbose_name='Status do Projeto'
    )
    plano_acao = models.TextField(
        verbose_name='Plano de Ação',
        blank=True,
        null=True,
        help_text='Plano de ação necessário quando o farol está crítico, atrasado ou em atenção, ou quando o custo realizado excede o planejado'
    )
    observacoes = models.TextField(verbose_name='Observações', blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Atualizado por')

    class Meta:
        verbose_name = 'Progresso do Projeto'
        verbose_name_plural = 'Progressos dos Projetos'
        ordering = ['-data']

    def __str__(self):
        return f"{self.projeto.nome} - {self.data.strftime('%d/%m/%Y')}"

    def clean(self):
        super().clean()
        if not self.projeto_id:
            raise ValidationError('É necessário selecionar um projeto.')
        
        try:
            projeto = Projeto.objects.get(id=self.projeto_id)
            if self.farol in ['CRITICO', 'ATRASADO', 'ATENCAO'] or self.custo_realizado > projeto.custo_planejado:
                if not self.plano_acao:
                    raise ValidationError('É necessário preencher o Plano de Ação quando o farol está crítico, atrasado ou em atenção, ou quando o custo realizado excede o planejado.')
            
            # Garantir que a diretoria do progresso seja a mesma do projeto
            if projeto and self.diretoria_id != projeto.diretoria_id:
                self.diretoria_id = projeto.diretoria_id
        except Projeto.DoesNotExist:
            raise ValidationError('Projeto selecionado não existe.')
