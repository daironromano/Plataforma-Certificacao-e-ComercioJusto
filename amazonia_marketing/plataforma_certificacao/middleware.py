"""
Middleware customizado para redirecionamento inteligente baseado em tipo de usuário.
Implementa fluxos de segurança e redirecionamento automático pós-login.
"""

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages


class RedirecionamentoPorTipoMiddleware(MiddlewareMixin):
    """
    Middleware que redireciona usuários autenticados para a página home correta
    baseado no seu tipo (produtor, empresa, admin).
    
    Verifica na cada requisição:
    1. Se usuário está autenticado
    2. Se tipo está definido
    3. Se está acessando uma URL pública desnecessariamente
    
    Fluxo:
    - /login/ → redireciona para dashboard correto
    - /home/ (pública) → redireciona para dashboard correto
    - /registration/ → redireciona para dashboard correto
    """
    
    # URLs públicas que podem ser acessadas mesmo autenticado
    URLS_PUBLICAS_PERMITIDAS = [
        '/admin/',
        '/api/',
        '/logout/',
        '/senha-recuperar/',
        '/verificar-email/',
        '/carrinho/',
        '/checkout/',
    ]
    
    # URLs que devem redirecionar se usuário estiver autenticado
    URLS_REDIRECIONA_SE_AUTENTICADO = [
        '/login/',
        '/registration/',
        '/cadastro/',
        '/home/',
    ]
    
    def process_request(self, request):
        """
        Intercepta requisição antes de chegar à view.
        Redireciona se necessário.
        """
        if not request.user.is_authenticated:
            return None
        
        path = request.path
        
        # Se está em URL de redirecionamento e está autenticado
        for url_pattern in self.URLS_REDIRECIONA_SE_AUTENTICADO:
            if path.startswith(url_pattern):
                # Importa aqui para evitar circular imports
                from .views import redirecionar_por_tipo
                return redirecionar_por_tipo(request.user)
        
        return None


class ValidacaoTipoUsuarioMiddleware(MiddlewareMixin):
    """
    Middleware que valida se o tipo do usuário está normalizado (minúsculas).
    Se encontrar tipo em MAIÚSCULAS ou CamelCase, normaliza automaticamente.
    """
    
    def process_request(self, request):
        """
        Verifica e normaliza tipo do usuário a cada requisição.
        """
        if not request.user.is_authenticated:
            return None
        
        # Verificar se tipo precisa ser normalizado
        if hasattr(request.user, 'tipo') and request.user.tipo:
            tipo_atual = request.user.tipo
            tipo_normalizado = tipo_atual.lower().strip()
            
            # Se não é minúsculo, normaliza
            if tipo_atual != tipo_normalizado:
                # Validar se tipo é válido
                tipos_validos = ['produtor', 'empresa', 'admin']
                if tipo_normalizado in tipos_validos:
                    # Atualiza no banco
                    request.user.tipo = tipo_normalizado
                    request.user.save()
        
        return None
