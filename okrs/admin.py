from django.contrib import admin
from .models import (
    TipoValor, Diretoria, Time, Objetivo, KeyResult, KeyResultProgresso,
    KPI, KPIProgresso, Projeto, ProjetoProgresso
)
from django import forms
from django.core.exceptions import ValidationError

@admin.register(Diretoria)
class DiretoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_criacao', 'ativo')
    list_filter = ('ativo', 'data_criacao')
    search_fields = ('nome', 'descricao')
    filter_horizontal = ('membros',)
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Membros', {
            'fields': ('membros',)
        }),
    )

@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'diretoria', 'data_criacao', 'ativo')
    list_filter = ('ativo', 'data_criacao', 'diretoria')
    search_fields = ('nome', 'descricao')
    filter_horizontal = ('membros',)
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'diretoria', 'descricao', 'ativo')
        }),
        ('Membros', {
            'fields': ('membros',)
        }),
    )

class KeyResultInline(admin.TabularInline):
    model = KeyResult
    extra = 1
    fields = ('descricao', 'tipo_valor', 'valor_target', 'ativo')

@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'time', 'diretoria', 'ano', 'data_criacao', 'ativo')
    list_filter = ('ativo', 'data_criacao', 'ano', 'time', 'time__diretoria')
    search_fields = ('descricao', 'time__nome', 'time__diretoria__nome')
    inlines = [KeyResultInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('time', 'descricao', 'ano', 'ativo')
        }),
    )

    def diretoria(self, obj):
        return obj.time.diretoria.nome
    diretoria.short_description = 'Diretoria'
    diretoria.admin_order_field = 'time__diretoria__nome'

class KeyResultProgressoInline(admin.TabularInline):
    model = KeyResultProgresso
    extra = 0
    fields = ('trimestre', 'valor_atual', 'data_atualizacao', 'atualizado_por')
    readonly_fields = ('data_atualizacao', 'atualizado_por')

@admin.register(KeyResult)
class KeyResultAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'objetivo', 'diretoria', 'tipo_valor', 'valor_target', 'ativo')
    list_filter = ('ativo', 'data_criacao', 'tipo_valor', 'objetivo__time', 'objetivo__time__diretoria')
    search_fields = ('descricao', 'objetivo__descricao', 'objetivo__time__diretoria__nome')
    inlines = [KeyResultProgressoInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('objetivo', 'descricao', 'tipo_valor', 'valor_target', 'ativo')
        }),
    )

    def diretoria(self, obj):
        return obj.objetivo.time.diretoria.nome
    diretoria.short_description = 'Diretoria'
    diretoria.admin_order_field = 'objetivo__time__diretoria__nome'
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Sobrescreve o método delete_selected para fazer a exclusão física
        for obj in queryset:
            obj.delete()
        self.message_user(request, f"{queryset.count()} KRs foram excluídos permanentemente.")
    delete_selected.short_description = "Excluir permanentemente os KRs selecionados"

class KeyResultProgressoForm(forms.ModelForm):
    class Meta:
        model = KeyResultProgresso
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        key_result = cleaned_data.get('key_result')
        data_progresso = cleaned_data.get('data_progresso')
        trimestre = cleaned_data.get('trimestre')
        
        if key_result and not self.instance.pk:  # Apenas para novos registros
            # Calcula o trimestre baseado na data do progresso
            mes = data_progresso.month
            if mes <= 3:
                trimestre = '1'
            elif mes <= 6:
                trimestre = '2'
            elif mes <= 9:
                trimestre = '3'
            else:
                trimestre = '4'
            
            # Verifica se já existe um registro para este KR neste trimestre
            existente = KeyResultProgresso.objects.filter(
                key_result=key_result,
                trimestre=trimestre
            ).first()
            
            if existente:
                raise ValidationError(
                    f'Já existe um registro de progresso para este Key Result no {trimestre}º trimestre. '
                    f'Por favor, edite o registro existente em vez de criar um novo.'
                )
        
        return cleaned_data

@admin.register(KeyResultProgresso)
class KeyResultProgressoAdmin(admin.ModelAdmin):
    form = KeyResultProgressoForm
    list_display = ('key_result', 'diretoria', 'data_progresso', 'trimestre', 'valor_atual', 'data_atualizacao', 'atualizado_por')
    list_filter = ('trimestre', 'data_atualizacao', 'data_progresso', 'key_result__objetivo__time', 'key_result__objetivo__time__diretoria')
    search_fields = ('key_result__descricao', 'key_result__objetivo__descricao', 'key_result__objetivo__time__diretoria__nome')
    readonly_fields = ('data_atualizacao',)
    change_form_template = 'admin/okrs/keyresultprogresso/change_form.html'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['key_result'].queryset = KeyResult.objects.filter(ativo=True)
        return form
    
    def get_fieldsets(self, request, obj=None):
        if not obj:  # Se for um novo objeto
            return (
                ('Informações Básicas', {
                    'fields': ('diretoria', 'key_result', 'data_progresso', 'valor_atual')
                }),
            )
        return (
            ('Informações Básicas', {
                'fields': ('diretoria', 'key_result', 'data_progresso', 'trimestre', 'valor_atual')
            }),
        )
    
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['atualizado_por'] = request.user.id
        return initial
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['diretorias'] = Diretoria.objects.filter(ativo=True)
        return super().changelist_view(request, extra_context)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['diretorias'] = Diretoria.objects.filter(ativo=True)
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def diretoria(self, obj):
        return obj.key_result.objetivo.time.diretoria.nome
    diretoria.short_description = 'Diretoria'
    diretoria.admin_order_field = 'key_result__objetivo__time__diretoria__nome'

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('nome', 'relevancia', 'tipo_valor', 'valor_target', 'ativo')
    list_filter = ('relevancia', 'tipo_valor', 'ativo')
    search_fields = ('nome', 'descricao', 'formula_calculo')
    ordering = ['-relevancia', 'nome']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'relevancia')
        }),
        ('Método de Cálculo', {
            'fields': ('formula_calculo', 'tipo_valor', 'valor_target')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

@admin.register(KPIProgresso)
class KPIProgressoAdmin(admin.ModelAdmin):
    list_display = ('kpi', 'valor_atual', 'data_medicao', 'data_atualizacao', 'atualizado_por')
    list_filter = ('kpi__relevancia', 'data_medicao')
    search_fields = ('kpi__nome', 'observacoes')
    ordering = ['-data_medicao']
    readonly_fields = ('data_atualizacao', 'atualizado_por', 'kpi_descricao', 'kpi_formula')
    change_form_template = 'admin/okrs/kpiprogresso/change_form.html'
    fieldsets = (
        ('Informações do KPI', {
            'fields': ('kpi', 'kpi_descricao', 'kpi_formula')
        }),
        ('Registro do Progresso', {
            'fields': ('valor_atual', 'data_medicao')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Informações do Sistema', {
            'fields': ('data_atualizacao', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )

    def kpi_descricao(self, obj):
        if obj and obj.kpi:
            return obj.kpi.descricao
        return "-"
    kpi_descricao.short_description = "Descrição do KPI"

    def kpi_formula(self, obj):
        if obj and obj.kpi:
            return obj.kpi.formula_calculo
        return "-"
    kpi_formula.short_description = "Fórmula de Cálculo"

    def save_model(self, request, obj, form, change):
        if not obj.atualizado_por:
            obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('admin/css/kpi_progresso.css',)
        }

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'diretoria', 'data_inicio', 'data_fim', 'custo_planejado', 'receita_planejada', 'ativo')
    list_filter = ('diretoria', 'ativo', 'cliente')
    search_fields = ('nome', 'descricao', 'cliente')
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cliente', 'descricao', 'diretoria')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Financeiro', {
            'fields': ('custo_planejado', 'receita_planejada')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

@admin.register(ProjetoProgresso)
class ProjetoProgressoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'data', 'farol', 'custo_realizado', 'receita_realizada')
    list_filter = ('projeto__diretoria', 'farol', 'data')
    search_fields = ('projeto__nome', 'observacoes', 'plano_acao')
    date_hierarchy = 'data'
    change_form_template = 'admin/okrs/projetoprogresso/change_form.html'
    
    fieldsets = (
        ('Informações do Projeto', {
            'fields': ('projeto', 'data')
        }),
        ('Progresso', {
            'fields': ('farol', 'custo_realizado', 'receita_realizada')
        }),
        ('Plano de Ação', {
            'fields': ('plano_acao',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Se estiver editando um objeto existente
            return ('data_atualizacao', 'atualizado_por')
        return ()

    def save_model(self, request, obj, form, change):
        if not change:  # Se for um novo objeto
            obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['projeto'].queryset = Projeto.objects.filter(ativo=True)
        return form

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['atualizado_por'] = request.user.id
        return initial

    class Media:
        js = ('admin/js/jquery.init.js',)
