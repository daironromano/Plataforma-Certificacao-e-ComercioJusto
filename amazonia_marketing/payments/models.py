from django.db import models
from django.conf import settings
from plataforma_certificacao.models import Pedido

class Pagamento(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
    )
    
    METODO_CHOICES = (
        ('cartao_credito', 'Cartão de Crédito'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
    )
    
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pagamento')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pagamentos')
    
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, default='cartao_credito')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    detalhes_resposta = models.JSONField(blank=True, null=True, default=dict)
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
    
    def __str__(self):
        return f'Pagamento {self.pk} - Pedido {self.pedido.pk} - {self.status}'
