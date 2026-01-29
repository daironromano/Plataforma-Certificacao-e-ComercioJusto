from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pagamento/<int:pedido_id>/', views.criar_sessao_pagamento, name='criar_sessao'),
    path('sucesso/<int:pedido_id>/', views.pagamento_sucesso, name='sucesso'),
    path('cancelado/<int:pedido_id>/', views.pagamento_cancelado, name='cancelado'),
    path('webhook/', views.webhook_stripe, name='webhook_stripe'),
    path('api/verificar/<int:pedido_id>/', views.verificar_status_pagamento, name='verificar_status'),
]