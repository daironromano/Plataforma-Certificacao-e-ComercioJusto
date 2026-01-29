from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
import stripe
import json

from plataforma_certificacao.models import Pedido, ItemPedido
from .models import Pagamento

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required(login_url='login')
def criar_sessao_pagamento(request, pedido_id):
    """
    Cria uma sessão de pagamento Stripe para um pedido específico
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    
    try:
        itens = ItemPedido.objects.filter(pedido=pedido)
        
        line_items = []
        for item in itens:
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': item.produto.nome,
                        'description': f'{item.quantidade}x',
                    },
                    'unit_amount': int(item.preco_unitario * 100),
                },
                'quantity': item.quantidade,
            })
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(f'/pedidos/{pedido_id}/sucesso/'),
            cancel_url=request.build_absolute_uri(f'/pedidos/{pedido_id}/cancelado/'),
            customer_email=request.user.email,
            metadata={
                'pedido_id': pedido_id,
                'usuario_id': request.user.id,
            }
        )
        
        pagamento, created = Pagamento.objects.get_or_create(
            pedido=pedido,
            defaults={
                'usuario': request.user,
                'valor': pedido.total,
                'metodo': 'cartao_credito',
                'stripe_session_id': session.id,
            }
        )
        
        if not created:
            pagamento.stripe_session_id = session.id
            pagamento.status = 'pendente'
            pagamento.save()
        
        return redirect(session.url, code=303)
    
    except stripe.error.StripeError as e:
        messages.error(request, f'Erro ao processar pagamento: {str(e)}')
        return redirect('checkout')


@login_required(login_url='login')
def pagamento_sucesso(request, pedido_id):
    """
    Página de sucesso após pagamento aprovado
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    pagamento = get_object_or_404(Pagamento, pedido=pedido)
    
    return render(request, 'payments/sucesso.html', {
        'pedido': pedido,
        'pagamento': pagamento,
    })


@login_required(login_url='login')
def pagamento_cancelado(request, pedido_id):
    """
    Página quando usuário cancela pagamento
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    pagamento = get_object_or_404(Pagamento, pedido=pedido)
    
    return render(request, 'payments/cancelado.html', {
        'pedido': pedido,
        'pagamento': pagamento,
    })


@csrf_exempt
def webhook_stripe(request):
    """
    Webhook para receber eventos de pagamento do Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Processar eventos de pagamento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        pedido_id = session['metadata'].get('pedido_id')
        
        try:
            pedido = Pedido.objects.get(pk=pedido_id)
            pagamento = Pagamento.objects.get(pedido=pedido)
            
            pagamento.status = 'aprovado'
            pagamento.stripe_payment_intent_id = session.get('payment_intent')
            pagamento.data_pagamento = timezone.now()
            pagamento.detalhes_resposta = session
            pagamento.save()
            
            pedido.status = 'pago'
            pedido.data_pagamento = timezone.now()
            pedido.save()
            
        except (Pedido.DoesNotExist, Pagamento.DoesNotExist):
            return JsonResponse({'error': 'Order not found'}, status=404)
    
    elif event['type'] == 'charge.failed':
        session = event['data']['object']
        payment_intent_id = session['payment_intent']
        
        try:
            pagamento = Pagamento.objects.get(stripe_payment_intent_id=payment_intent_id)
            pagamento.status = 'rejeitado'
            pagamento.detalhes_resposta = session
            pagamento.save()
        except Pagamento.DoesNotExist:
            pass
    
    return JsonResponse({'status': 'success'}, status=200)


def verificar_status_pagamento(request, pedido_id):
    """
    API para verificar status em tempo real do pagamento
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    try:
        pagamento = Pagamento.objects.get(pedido=pedido)
        
        return JsonResponse({
            'status': pagamento.status,
            'metodo': pagamento.metodo,
            'valor': float(pagamento.valor),
            'data_pagamento': pagamento.data_pagamento.isoformat() if pagamento.data_pagamento else None,
        })
    except Pagamento.DoesNotExist:
        return JsonResponse({'status': 'nao_encontrado'}, status=404)