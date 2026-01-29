"""
Segurança: Proteção contra IDOR e Controle de Acesso.
Implementa validações de propriedade de recurso e filtros de segurança.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from .models import Produtos, Certificacoes, Pedido, UsuarioBase


class IDORProtectionMixin:
    """
    Mixin para proteção contra IDOR em views baseadas em classe.
    Valida que o usuário logado é o dono do recurso antes de permitir acesso.
    
    Uso:
        class MeuDetalheProduto(IDORProtectionMixin, DetailView):
            model = Produtos
            pk_url_kwarg = 'produto_id'
            owner_field = 'usuario'
    """
    owner_field = 'usuario'  # Campo que contém a relação com o usuário
    
    def get_object(self):
        """Sobrescreve get_object para validar propriedade."""
        obj = super().get_object()
        
        # Validar que o usuário é o dono do objeto
        owner = getattr(obj, self.owner_field)
        if owner != self.request.user:
            messages.error(self.request, 'Acesso negado: Este recurso não pertence a você.')
            raise PermissionError("Acesso negado")
        
        return obj


def validar_propriedade_produto(view_func):
    """
    Decorador que valida se o usuário logado é o dono do produto.
    Protege contra IDOR em views baseadas em função.
    
    Uso:
        @validar_propriedade_produto
        def editar_produto(request, produto_id):
            produto = request.context['produto']
            ...
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        produto_id = kwargs.get('produto_id')
        
        if not produto_id:
            messages.error(request, 'Produto não especificado.')
            return redirect('home_publica')
        
        # IDOR Protection: Filtra apenas produtos do usuário logado
        produto = get_object_or_404(Produtos, id_produto=produto_id, usuario=request.user)
        
        # Passa o produto para a view
        kwargs['produto_obj'] = produto
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validar_propriedade_certificacao(view_func):
    """
    Decorador que valida se o usuário logado tem acesso à certificação.
    Para produtores: valida que a certificação é de um produto seu.
    Para admins: todos têm acesso.
    
    Uso:
        @validar_propriedade_certificacao
        def detalhe_certificacao(request, certificacao_id):
            certificacao = request.context['certificacao']
            ...
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        certificacao_id = kwargs.get('certificacao_id')
        
        if not certificacao_id:
            messages.error(request, 'Certificação não especificada.')
            return redirect('home_publica')
        
        # Admins têm acesso a todas as certificações
        if request.user.tipo == 'admin':
            certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
        else:
            # Produtores: Apenas certificações dos seus produtos
            certificacao = get_object_or_404(
                Certificacoes,
                id_certificacao=certificacao_id,
                produto__usuario=request.user
            )
        
        # Passa a certificação para a view
        kwargs['certificacao_obj'] = certificacao
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validar_propriedade_pedido(view_func):
    """
    Decorador que valida se o usuário logado é o dono do pedido.
    Protege contra IDOR em consulta de pedidos.
    
    Uso:
        @validar_propriedade_pedido
        def detalhes_pedido(request, pedido_id):
            pedido = request.context['pedido']
            ...
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        pedido_id = kwargs.get('pedido_id')
        
        if not pedido_id:
            messages.error(request, 'Pedido não especificado.')
            return redirect('home_publica')
        
        # IDOR Protection: Filtra apenas pedidos do usuário logado
        pedido = get_object_or_404(Pedido, id_pedido=pedido_id, usuario=request.user)
        
        # Passa o pedido para a view
        kwargs['pedido_obj'] = pedido
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validar_propriedade_carrinho(view_func):
    """
    Decorador que valida se o usuário logado é o dono do carrinho.
    
    Uso:
        @validar_propriedade_carrinho
        def visualizar_carrinho(request):
            carrinho = request.context['carrinho']
            ...
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        # IDOR Protection: Filtra apenas carrinho do usuário logado
        kwargs['carrinho_user'] = request.user
        return view_func(request, *args, **kwargs)
    
    return wrapper


def requires_owner_or_admin(resource_model, id_param='id', owner_field='usuario'):
    """
    Decorador genérico para validar propriedade de recurso ou acesso admin.
    
    Args:
        resource_model: Modelo do recurso (ex: Produtos)
        id_param: Nome do parâmetro de ID na URL (ex: 'produto_id')
        owner_field: Campo que contém o usuário dono
    
    Uso:
        @requires_owner_or_admin(Produtos, 'produto_id', 'usuario')
        def editar_produto(request, produto_id):
            recurso = request.context['recurso']
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            resource_id = kwargs.get(id_param)
            
            if not resource_id:
                messages.error(request, f'{resource_model.__name__} não especificado.')
                return redirect('home_publica')
            
            # Buscar o recurso
            try:
                recurso = resource_model.objects.get(pk=resource_id)
            except resource_model.DoesNotExist:
                messages.error(request, f'{resource_model.__name__} não encontrado.')
                return redirect('home_publica')
            
            # Validar propriedade: Dono ou Admin
            owner = getattr(recurso, owner_field, None)
            if owner != request.user and request.user.tipo != 'admin':
                messages.error(request, 'Acesso negado: Este recurso não pertence a você.')
                return redirect('home_publica')
            
            # Passa o recurso para a view
            kwargs['recurso_obj'] = recurso
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def filter_queryset_by_user(queryset, user, user_field='usuario'):
    """
    Função auxiliar para filtrar queryset apenas para o usuário logado.
    Protege contra IDOR em querysets.
    
    Uso:
        produtos = Produtos.objects.all()
        produtos_do_user = filter_queryset_by_user(produtos, request.user)
    
    Args:
        queryset: QuerySet a ser filtrado
        user: Usuário logado (request.user)
        user_field: Nome do campo de usuário no modelo
    
    Returns:
        QuerySet filtrado apenas para o usuário
    """
    if user and user.is_authenticated:
        return queryset.filter(**{user_field: user})
    return queryset.none()


def secure_get_object(model, user, object_id, user_field='usuario', pk_field='pk'):
    """
    Função auxiliar para buscar um objeto com proteção IDOR.
    
    Uso:
        produto = secure_get_object(
            Produtos, 
            request.user, 
            produto_id,
            user_field='usuario',
            pk_field='id_produto'
        )
    
    Args:
        model: Modelo (ex: Produtos)
        user: Usuário logado
        object_id: ID do objeto
        user_field: Nome do campo de usuário no modelo
        pk_field: Nome do campo primário
    
    Returns:
        Objeto ou None se acesso negado
    
    Raises:
        PermissionError: Se usuário não tem permissão
    """
    try:
        filter_kwargs = {pk_field: object_id, user_field: user}
        obj = model.objects.get(**filter_kwargs)
        return obj
    except model.DoesNotExist:
        raise PermissionError(f"Acesso negado ou {model.__name__} não encontrado.")
