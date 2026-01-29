from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PlataformaCertificacaoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plataforma_certificacao'

    def ready(self):
        def criar_grupos(sender, **kwargs):
            from django.contrib.auth.models import Group

            grupos = ['Produtor', 'Empresa', 'Auditor/Admin']
            for nome in grupos:
                Group.objects.get_or_create(name=nome)

        post_migrate.connect(criar_grupos, sender=self)
