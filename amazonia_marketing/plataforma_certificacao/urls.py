from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [   
    path('', views.home_publica, name='home_publica'), # Essa é a rota da tela inicial para sem logar
    path('registration/login/', views.login_usuarios, name='login'), # Rota para usuários cadastrados
    path('registration/cadastro/', views.cadastro_usuario, name='cadastro'), # Rota para cadastrar usuários    
    path('produtor/dashboard/', views.home_produtor, name='home_produtor'), # Rota protegida: produtor
    path('empresa/dashboard/', views.home_empresa, name='home_empresa'), # Rota protegida: empresa
    path('auditoria/dashboard', views.home_admin, name='home_admin'), # Rota protegida: admin
    path('home/', views.home_publica, name='home_publica'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro_produto/', views.cadastro_produto, name='cadastro_produto'),
    path('produtor/certificado/', views.enviar_autodeclaracao, name='enviar_autodeclaracao' ),
    path('produtor/deletar/<int:produto_id>', views.deletar_produto, name='deletar_produto'),
    path('auditoria/visualizar/', views.admin_visualizar_certificados, name='admin_visualizar_certificacoes'),
    path('auditoria/responder/<int:certificacao_id>', views.admin_responder_certificacoes, name='admin_responder_certificacao')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)