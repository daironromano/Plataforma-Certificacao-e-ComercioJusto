from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    """
    Backend de autenticação customizado que permite login com email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Tenta buscar o usuário pelo username (que no nosso caso é o email)
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Se não encontrar, tenta buscar pelo campo email
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
        
        # Verifica a senha
        if user.check_password(password):
            return user
        return None
