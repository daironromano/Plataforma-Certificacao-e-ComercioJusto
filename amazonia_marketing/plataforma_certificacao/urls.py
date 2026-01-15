from django.urls import path
from . import views


urlpatterns = [   
    path('', views.login_usuarios, name='login'), # Raiz é o login
    path('produtor/', views.home_produtor, name='home_produtor'),
    path('empresa/', views.home_empresa, name='home_empresa'),
    path('auditoria/', views.home_admin, name='home_admin'),
    path('home/', views.home_padrao, name='home_padrao'),
    path('logout/', views.logout_view, name='logout'),
]