from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [   
    path('', views.home_publica, name='home_publica'), # Tela inicial pública
    
    # Rotas de Autenticação e Cadastro
    path('registration/login/', views.login_usuarios, name='login'),
    path('registration/escolher-tipo/', views.escolher_tipo_cadastro, name='escolher_tipo_cadastro'),
    path('registration/escolher-tipo-google/', views.escolher_tipo_apos_google, name='escolher_tipo_google'),
    path('registration/cadastro-produtor/', views.cadastro_produtor, name='cadastro_produtor'),
    path('registration/cadastro-empresa/', views.cadastro_empresa, name='cadastro_empresa'),
    path('logout/', views.logout_view, name='logout'),
    
    # Rotas protegidas por tipo de usuário
    path('produtor/dashboard/', views.home_produtor, name='home_produtor'),
    path('empresa/dashboard/', views.home_empresa, name='home_empresa'),
    path('auditoria/dashboard', views.home_admin, name='home_admin'),
    
    # Rotas de funcionalidades do Produtor
    path('cadastro_produto/', views.cadastro_produto, name='cadastro_produto'),
    path('produtor/certificado/', views.enviar_autodeclaracao, name='enviar_autodeclaracao'),
    path('produtor/certificado-multiplo/', views.enviar_autodeclaracao_multipla, name='enviar_autodeclaracao_multipla'),
    path('produtor/deletar/<int:produto_id>', views.deletar_produto, name='deletar_produto'),
    path('produtor/configuracoes/', views.config_perfil_produtor, name='config_perfil_produtor'),
    
    # Rotas de funcionalidades da Empresa
    path('empresa/configuracoes/', views.config_perfil_empresa, name='config_perfil_empresa'),
    
    # Rotas de funcionalidades do Admin/Auditor
    path('auditoria/visualizar/', views.admin_visualizar_certificados, name='admin_visualizar_certificacoes'),
    path('auditoria/responder/<int:certificacao_id>', views.admin_responder_certificacoes, name='admin_responder_certificacao'),
    path('auditoria/certificacao/<int:certificacao_id>/', views.detalhe_certificacao, name='detalhe_certificacao'),
    path('auditoria/pendentes/', views.lista_certificacoes_pendentes, name='lista_certificacoes_pendentes'),
    path('auditoria/aprovadas/', views.lista_certificacoes_aprovadas, name='lista_certificacoes_aprovadas'),
    path('auditoria/reprovadas/', views.lista_certificacoes_reprovadas, name='lista_certificacoes_reprovadas'),
    
    # Rotas de Empresas (Admin)
    path('auditoria/empresas/pendentes/', views.lista_empresas_pendentes, name='lista_empresas_pendentes'),
    path('auditoria/empresas/verificadas/', views.lista_empresas_verificadas, name='lista_empresas_verificadas'),
    path('auditoria/empresas/rejeitadas/', views.lista_empresas_rejeitadas, name='lista_empresas_rejeitadas'),
    path('auditoria/empresas/<int:empresa_id>/', views.detalhe_empresa, name='detalhe_empresa'),
    
    # API de validação
    path('validar-cnpj/', views.validar_cnpj_api, name='validar_cnpj'),
    
    # Rotas de Carrinho e Checkout
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/remover/<int:item_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/atualizar/<int:item_id>/', views.atualizar_quantidade_carrinho, name='atualizar_quantidade_carrinho'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedidos/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    
    # Rotas de Marketplace Externo
    path('marketplace/gerar/<int:produto_id>/', views.gerar_anuncio_marketplace, name='gerar_anuncio_marketplace'),
    path('marketplace/anuncio/<int:anuncio_id>/', views.visualizar_anuncio, name='visualizar_anuncio'),
    path('marketplace/meus-anuncios/', views.meus_anuncios, name='meus_anuncios'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)