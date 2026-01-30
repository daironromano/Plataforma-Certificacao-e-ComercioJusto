from django.contrib import admin
from .models import Pagamento

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('pk', 'usuario', 'pedido', 'metodo', 'valor', 'status', 'data_criacao')
    list_filter = ('status', 'metodo', 'data_criacao')
    search_fields = ('usuario__email', 'pedido__pk', 'stripe_session_id', 'stripe_payment_intent_id')
    readonly_fields = ('stripe_session_id', 'stripe_payment_intent_id', 'data_criacao', 'data_atualizacao', 'detalhes_resposta')
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('pedido', 'usuario', 'valor')
        }),
        ('Pagamento', {
            'fields': ('metodo', 'status', 'data_pagamento')
        }),
        ('Stripe', {
            'fields': ('stripe_session_id', 'stripe_payment_intent_id')
        }),
        ('Dados Adicionais', {
            'fields': ('detalhes_resposta', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request):
        return False

