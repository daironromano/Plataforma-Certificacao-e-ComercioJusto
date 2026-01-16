"""
URL configuration for backend_amazonia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
<<<<<<< Updated upstream:Códigos/Backend/backend_amazonia/backend_amazonia/urls.py
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'), # Raiz é o login
=======
from django.conf import settings
from django.conf.urls.static import static
from plataforma_certificacao import views

urlpatterns = [
    path('', views.login_usuarios, name='login'),
>>>>>>> Stashed changes:amazonia_marketing/amazonia_marketing/urls.py
    path('produtor/', views.home_produtor, name='home_produtor'),
    path('auditoria/', views.home_admin, name='home_admin'),
    path('home/', views.home_padrao, name='home_padrao'),
    path('logout/', views.logout_view, name='logout'),
    
    # URLs para Upload de Autodeclaração
    path('produtor/enviar-autodeclaracao/', views.enviar_autodeclaracao, name='enviar_autodeclaracao'),
    path('produtor/certificacoes/', views.ver_certificacoes, name='ver_certificacoes'),
    path('produtor/certificacao/<int:certificacao_id>/download/', views.baixar_arquivo_certificacao, name='baixar_arquivo_certificacao'),
    
    # URLs para Admin (ANTES do Django Admin para não ser capturado)
    path('admin/certificacoes/', views.admin_visualizar_certificacoes, name='admin_visualizar_certificacoes'),
    path('admin/certificacao/<int:certificacao_id>/responder/', views.admin_responder_certificacao, name='admin_responder_certificacao'),
    
    # Django Admin (deve vir por último)
    path('admin/', admin.site.urls),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)