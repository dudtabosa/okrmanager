from django.contrib import admin
from .models import Diretoria, Time, Objetivo, KeyResult, KeyResultProgresso

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

class KeyResultProgressoAdmin(admin.ModelAdmin):
    list_display = ('key_result', 'diretoria', 'trimestre', 'valor_atual', 'data_atualizacao', 'atualizado_por')
    list_filter = ('trimestre', 'data_atualizacao', 'key_result__objetivo__time', 'key_result__objetivo__time__diretoria')
    search_fields = ('key_result__descricao', 'key_result__objetivo__descricao', 'key_result__objetivo__time__diretoria__nome')
    readonly_fields = ('data_atualizacao',)

    def diretoria(self, obj):
        return obj.key_result.objetivo.time.diretoria.nome
    diretoria.short_description = 'Diretoria'
    diretoria.admin_order_field = 'key_result__objetivo__time__diretoria__nome'

admin.site.register(Diretoria, DiretoriaAdmin)
admin.site.register(Time, TimeAdmin)
admin.site.register(Objetivo, ObjetivoAdmin)
admin.site.register(KeyResult, KeyResultAdmin)
admin.site.register(KeyResultProgresso, KeyResultProgressoAdmin)
