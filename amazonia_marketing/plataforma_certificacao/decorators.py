"""
Decoradores customizados para segurança e controle de acesso.
Implementa proteção contra IDOR, validação de grupos e permissões.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from .models import CustomUser, Produtos, Certificacoes
from allauth.account.decorators import verified_email_required

@verified_email_required
def verified_email_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.email_verified:
            return redirect('email_nao_verificado')

        return view_func(request, *args, **kwargs)
    return wrapper

def group_required(group_name):
    """
    Decorador que valida se o usuário pertence a um grupo específico.
    
    Uso:
        @group_required('Produtor')
        def minha_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            # Obtém os grupos do usuário
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            
            # Acesso negado
            messages.error(request, f'Acesso negado. Você precisa ser um {group_name} para acessar esta área.')
            return redirect('home_publica')
        
        return wrapper
    return decorator


def user_is_produtor(view_func):
    """
    Decorador específico para proteger views de Produtor.
    Valida tipo de usuário via CustomUser.tipo
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        # Validação: Verificar se usuário é produtor
        if hasattr(request.user, 'tipo') and request.user.tipo == 'produtor':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Apenas produtores podem acessar esta área.')
            return redirect('home_publica')
    
    return wrapper


def user_is_empresa(view_func):
    """
    Decorador específico para proteger views de Empresa.
    Valida tipo de usuário via CustomUser.tipo
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        # Validação: Verificar se usuário é empresa
        if hasattr(request.user, 'tipo') and request.user.tipo == 'empresa':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Apenas empresas podem acessar esta área.')
            return redirect('home_publica')
    
    return wrapper


def user_is_admin(view_func):
    """
    Decorador específico para proteger views de Admin/Auditor.
    Valida tipo de usuário via CustomUser.tipo
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        # Validação: Verificar se usuário é admin
        if hasattr(request.user, 'tipo') and request.user.tipo == 'admin':
            return view_func(request, *args, **kwargs)
        elif request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Apenas auditores podem acessar esta área.')
            return redirect('home_publica')
    
    return wrapper


def owns_produto(view_func):
    """
    Decorador que protege contra IDOR (Insecure Direct Object References).
    Valida se o usuário logado é o dono do produto antes de permitir acesso.
    
    Uso esperado:
        @owns_produto
        def editar_produto(request, produto_id):
            ...
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        produto_id = kwargs.get('produto_id')
        
        if not produto_id:
            raise Http404("Produto não encontrado.")
        
        try:
            # Filtra apenas produtos do usuário logado
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                # Se não tem na sessão, tenta pegar do User model
                usuario = CustomUser.objects.get(user=request.user)
                usuario_id = usuario.id_usuario
            
            # SEGURANÇA: Filtra pelo dono (IDOR prevention)
            produto = Produtos.objects.get(id_produto=produto_id, usuario_id=usuario_id)
        
        except Produtos.DoesNotExist:
            messages.error(request, 'Acesso negado. Este produto não pertence a você.')
            raise Http404("Acesso negado ao recurso.")
        
        # Passa o produto para a view
        kwargs['produto'] = produto
        return view_func(request, *args, **kwargs)
    
    return wrapper


def owns_certificacao(view_func):
    """
    Decorador que protege contra IDOR para certificações.
    Valida se o usuário logado é o responsável (admin) pela certificação.
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapper(request, *args, **kwargs):
        certificacao_id = kwargs.get('certificacao_id')
        
        if not certificacao_id:
            raise Http404("Certificação não encontrada.")
        
        try:
            # Obtém o ID do usuário da sessão
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                usuario = CustomUser.objects.get(user=request.user)
                usuario_id = usuario.id_usuario
            
            # SEGURANÇA: Valida se é o admin responsável
            certificacao = Certificacoes.objects.get(id_certificacao=certificacao_id)
            
            # Apenas o admin responsável pode editar
            if certificacao.admin_responsavel_id != usuario_id and request.session.get('usuario_tipo') != 'admin':
                raise Http404("Você não tem permissão para editar esta certificação.")
        
        except Certificacoes.DoesNotExist:
            raise Http404("Certificação não encontrada.")
        
        kwargs['certificacao'] = certificacao
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_usuario_session(request):
    """
    Função auxiliar para obter o CustomUser a partir da sessão.
    Compatível com OAuth e login manual.
    """
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            return CustomUser.objects.get(id_usuario=usuario_id)
        except CustomUser.DoesNotExist:
            pass
    
    # Fallback para User model
    if request.user.is_authenticated:
        try:
            return CustomUser.objects.get(user=request.user)
        except CustomUser.DoesNotExist:
            pass
    
    return None
