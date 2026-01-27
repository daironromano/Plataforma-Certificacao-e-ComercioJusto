from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [   
    path('', views.home_publica, name='home_publica'),
    path('registration/login/', views.login_usuarios, name='login'),
    path('registration/cadastro/', views.cadastro_usuario, name='cadastro'),    
    
    # Rotas do Produtor
    path('produtor/dashboard/', views.home_produtor, name='home_produtor'),
    path('produtor/perfil/editar/', views.editar_perfil_produtor, name='editar_perfil_produtor'),
    path('produtor/certificado/', views.enviar_autodeclaracao, name='enviar_autodeclaracao'),
    path('produtor/deletar/<int:produto_id>', views.deletar_produto, name='deletar_produto'),
    path('cadastro_produto/', views.cadastro_produto, name='cadastro_produto'),

    # Rota da Empresa
    path('empresa/dashboard/', views.home_empresa, name='home_empresa'),

    # Rotas da Auditoria (ADMIN)
    path('auditoria/dashboard', views.home_admin, name='home_admin'),
    
    # --- CORREÇÃO AQUI ---
    # Mudamos o name para terminar em 'certificados' (DOS) para bater com o template
    path('auditoria/visualizar/', views.admin_visualizar_certificados, name='admin_visualizar_certificados'),
    
    path('auditoria/analise/<int:certificacao_id>/', views.admin_detalhes_certificacao, name='admin_detalhes'),
    path('auditoria/responder/<int:certificacao_id>/', views.admin_responder_certificacoes, name='admin_responder_certificacoes'),

    # Rotas Utilitárias
    path('logout/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)