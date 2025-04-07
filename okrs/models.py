from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.

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
