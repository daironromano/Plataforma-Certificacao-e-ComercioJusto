"""
Adapters customizados para django-allauth.
Mapeiam dados do Google OAuth para o modelo UsuarioBase.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter, get_adapter
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from .models import UsuarioBase, ProdutorProfile, EmpresaProfile


def normalize_tipo(tipo_input):
    """
    Normaliza o tipo de usuário para minúsculas.
    Valida se está entre as opções permitidas.
    
    Aceita: "produtor", "PRODUTOR", "Produtor", "PrOdUtoR", etc.
    Retorna: "produtor" (minúsculas) ou None se inválido
    """
    if not tipo_input:
        return None
    
    tipos_validos = ['produtor', 'empresa', 'admin']
    tipo_normalizado = str(tipo_input).strip().lower()
    
    # Validar se é uma opção válida
    if tipo_normalizado not in tipos_validos:
        return None
    
    return tipo_normalizado


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter customizado para mapear dados do Google para UsuarioBase.
    Permite que o usuário escolha se é Produtor ou Empresa após login social.
    """
    
    def pre_social_login(self, request, sociallogin):

        super().pre_social_login(request, sociallogin)

        """
        Chamado antes do login social ser completado.
        Aqui verificamos se já existe um usuário com o email do Google.
        """
        # Se o usuário já está conectado a uma conta, não faz nada
        if sociallogin.is_existing:
            return
        
        # Pega o email do Google
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return
        
        # Verifica se já existe um usuário Django com esse email
        try:
            user = UsuarioBase.objects.get(email__iexact=email)
            # Encontrou! Conecta a conta social ao usuário existente
            # Isso permite que um usuário que se cadastrou manualmente
            # possa fazer login com Google depois
            sociallogin.connect(request, user)
            raise ImmediateHttpResponse(redirect(self.get_login_redirect_url(request)))
        except UsuarioBase.DoesNotExist:
            # Usuário novo - se ele ainda não escolheu o tipo, pausamos o fluxo
            if not request.session.get('tipo_usuario_social'):
                # Guarda dados mínimos para mostrar na tela de escolha
                request.session['google_data'] = {
                    'email': email,
                    'nome': sociallogin.account.extra_data.get('name', email.split('@')[0]),
                    'picture': sociallogin.account.extra_data.get('picture', ''),
                }
                # Armazena o sociallogin para resgatar após a escolha de perfil
                self.stash_sociallogin(request, sociallogin)
                super().pre_social_login(request, sociallogin)
                raise ImmediateHttpResponse(redirect(reverse('escolher_tipo_google')))

    def stash_sociallogin(self, request, sociallogin):
        """Serializa e guarda o sociallogin na sessão."""
        request.session['socialaccount_sociallogin'] = sociallogin.serialize()

    def unstash_sociallogin(self, request):
        """Recupera o sociallogin serializado da sessão sem removê-lo."""
        data = request.session.get('socialaccount_sociallogin')
        if not data:
            return None
        try:
            return SocialLogin.deserialize(data)
        except Exception:
            return None

    def clear_stashed_sociallogin(self, request):
        """Remove o sociallogin armazenado na sessão."""
        request.session.pop('socialaccount_sociallogin', None)
    
    def save_user(self, request, sociallogin, form=None):
        """
        Salva o usuário após login social.
        Aqui criamos o UsuarioBase e perfis específicos com dados do Google.
        """
        # Pega dados do Google
        google_data = sociallogin.account.extra_data
        email = google_data.get('email')
        nome = google_data.get('name', email.split('@')[0])  # Usa parte antes do @ se não tiver nome
        
        # Verifica se o usuário já escolheu o tipo e normaliza
        tipo = request.session.get('tipo_usuario_social', None)
        tipo_normalizado = normalize_tipo(tipo)
        
        if not tipo_normalizado:
            # Segurança extra: se chegou aqui sem tipo válido, pausa e volta para escolha
            request.session['google_data'] = {
                'email': email,
                'nome': nome,
                'picture': google_data.get('picture', ''),
            }
            raise ImmediateHttpResponse(redirect(reverse('escolher_tipo_google')))
        
        # Chama a implementação padrão do save_user que cria o UsuarioBase
        # Este método já foi populado pelo populate_user
        user = super().save_user(request, sociallogin, form)
        
        # IMPORTANTE: user já foi salvo pela super().save_user()
        # Atualizar o tipo de usuário no UsuarioBase com valor normalizado
        user.tipo = tipo_normalizado
        user.nome = nome
        user.save()
        
        # Se foi criado novo, cria o perfil específico (Produtor ou Empresa)
        if tipo_normalizado == 'produtor':
            ProdutorProfile.objects.get_or_create(usuario=user)
        elif tipo_normalizado == 'empresa':
            EmpresaProfile.objects.get_or_create(usuario=user)
        
        # Limpa dados da sessão
        if 'tipo_usuario_social' in request.session:
            del request.session['tipo_usuario_social']
        if 'google_data' in request.session:
            del request.session['google_data']
        self.clear_stashed_sociallogin(request)
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Popula o objeto de usuário com dados do provider social.
        Chamado antes de save_user.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Aqui podemos adicionar campos extras se necessário
        # Por exemplo, se UsuarioBase tivesse campos como first_name, last_name
        extra_data = sociallogin.account.extra_data
        
        # Exemplo de campos que poderiam ser populados:
        # user.first_name = extra_data.get('given_name', '')
        # user.last_name = extra_data.get('family_name', '')
        
        return user
    
    def get_login_redirect_url(self, request):
        """
        Define para onde redirecionar após login bem-sucedido.
        """
        # Se tem dados do Google na sessão, vai para escolher tipo
        if 'google_data' in request.session:
            return '/registration/escolher-tipo-google/'
        
        # Senão, redireciona baseado no tipo de usuário
        if request.user and request.user.is_authenticated:
            tipo = getattr(request.user, 'tipo', None)
            
            if tipo:
                tipo = tipo.lower()
                if tipo == 'produtor':
                    return '/produtor/dashboard/'
                elif tipo == 'empresa':
                    return '/empresa/dashboard/'
                elif tipo == 'admin':
                    return '/admin/dashboard/'
        
        # Fallback para página inicial
        return '/'
