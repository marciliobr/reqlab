from django.contrib import admin

from .models import *


@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'sala', 'status', 'escopo')
    list_filter = ('escopo', 'status', )
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'is_active',
                    'is_professor', 'is_staff','escopo_default')
    list_filter = ('is_active', 'is_staff', 'is_professor', 'escopo_default')
    exclude = ['groups', 'user_permissions', 'is_superuser',
               'password']
    readonly_fields = ('last_login', 'date_joined')
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):

    list_display = ('codigo', 'descricao', 'status')
    list_filter = ('status', )
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'tipo', 'status', 'estoque', 'escopo')
    list_filter = ('tipo', 'escopo', 'status', )
    search_fields = ('nome',)
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Ferramenta)
class FerramentaAdmin(admin.ModelAdmin):
    list_display = ('item', 'tombo', 'status')
    list_filter = ('item', 'status', )
    search_fields = ('tombo', 'item__nome')
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EstoqueMaterial)
class EstoqueMaterialAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantidade')
    search_fields = ('item__nome', )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HistoricoEstoque)
class HistoricoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'item', 'quantidade',
                    'estoque_anterior', 'descricao', 'requisicao')
    search_fields = ('item__nome', )
    list_filter = ('data_hora',)
    exclude = ('estoque_anterior', 'requisicao')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Requisicao)
class RequisicaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'escopo', 'laboratorio', 'tipo_atividade', 'professor',
                    'data', 'hora_inicio', 'status')
    list_filter = ('escopo', 'laboratorio', 'tipo_atividade',
                   'professor', 'data', 'status', )
    readonly_fields = ('escopo', 'ocorrencias', 'status', 'observacoes', 'professor')
    exclude = ('itens', 'itens_json',)
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'escopo', 'inicio', 'fim', 'importante', 'status')
    list_filter = ('escopo', 'inicio', 'fim', 'importante', 'status', )
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfigLab)
class ConfigLabAdmin(admin.ModelAdmin):
    list_display = ('configuracao', 'valor')

    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Escopo)
class EscopoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'status')
    # Desabilitar delete

    def has_delete_permission(self, request, obj=None):
        return False
