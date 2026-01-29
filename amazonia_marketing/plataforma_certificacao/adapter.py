"""
Adapter alternativo simplificado para integração com Google OAuth.
NOTA: O sistema já usa 'adapters.py' com CustomSocialAccountAdapter.
Este arquivo é mantido como referência para customizações adicionais.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter customizado para integração com Google OAuth.
    Gerencia o fluxo de login social e mapeamento de dados do usuário.
    
    ATENÇÃO: O sistema já utiliza CustomSocialAccountAdapter em adapters.py
    Este arquivo serve como exemplo de implementação alternativa.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Lógica executada antes do login ser concluído.
        Permite customizar o mapeamento de dados do Google para o sistema.
        """
        user = sociallogin.user
        
        # Se é um novo usuário (ainda não tem ID no banco)
        if not user.id:
            # sociallogin.account.extra_data contém todo o JSON do Google
            # Exemplos de dados disponíveis:
            # - extra_data['email']: Email do usuário
            # - extra_data['name']: Nome completo
            # - extra_data['given_name']: Primeiro nome
            # - extra_data['family_name']: Sobrenome
            # - extra_data['picture']: URL da foto de perfil
            
            # Armazena dados do Google na sessão para uso posterior
            extra_data = sociallogin.account.extra_data
            request.session['google_data'] = {
                'nome': extra_data.get('name', ''),
                'email': extra_data.get('email', ''),
                'picture': extra_data.get('picture', ''),
                'given_name': extra_data.get('given_name', ''),
                'family_name': extra_data.get('family_name', ''),
            }
    
    def save_user(self, request, sociallogin, form=None):
        """
        Salva ou atualiza o usuário após login social.
        Aqui podemos customizar como os dados do Google são mapeados para o CustomUser.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Pegar tipo de usuário escolhido na sessão (se houver)
        tipo_usuario = request.session.get('tipo_usuario_social', None)
        
        if tipo_usuario:
            user.tipo = tipo_usuario
            user.save()
            # Limpa a sessão após usar
            del request.session['tipo_usuario_social']
        
        # Mapear dados do Google para campos customizados
        extra_data = sociallogin.account.extra_data
        
        if not user.nome:  # Se o nome ainda não foi definido
            user.nome = extra_data.get('name', '')
        
        user.save()
        
        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Controla se o cadastro automático via Google está permitido.
        Retorna False para forçar o usuário a escolher o tipo (Produtor/Empresa).
        """
        # Se já existe tipo definido na sessão, permite auto-signup
        if 'tipo_usuario_social' in request.session:
            return True
        
        # Caso contrário, redireciona para escolha de tipo
        return False

