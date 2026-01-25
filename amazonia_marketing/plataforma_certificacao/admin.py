from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

# Essa configuração permite que os campos de usuário sejam mostrados
# na tabela usuários ao criar um cadastro.
class ProdutorInline(admin.StackedInline):
    model = PerfilProduto
    can_delete = False
    verbonse_name_plural = 'Perfil de Produtor'
    
class EmpresaInline(admin.StackedInline):
    model = PerfilEmpresa
    can_dalete = False
    verbose_name_plural = 'Perfil de Empresa'
    
# Personlaizando o painel administrativo do usuário 'Customuser'
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_staff')
    # Filtros laterais adicionados
    list_filter = ('tipo_usuario', 'is_staff', 'is_superuser')
    # Adicionando os inlines criados em cima
    inlines = (ProdutorInline, EmpresaInline)
    # Configurando campos que aparecem ao editar
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {'fields': ('tipo_usuario',)}),
    )
    
    # Configurações dos campos que aparecem ao criar
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Extras', {'fields': ('tipo_usuario',)}),
    )
    
# REGISTRANDO MODELOS NO PAINEL
# Registra o usuário com a configuração avançada acima
admin.site.register(CustomUser, CustomUserAdmin)

# Registra os produtos
@admin.register(Produtos)
class ProdutosAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco', 'status_estoque', 'usuario')
    search_fields = ('nome', 'categoria')
    list_filter = ('status_estoque', 'categoria')
    
# Registra os certificados
@admin.register(Certificacoes)
class CertificacoesAdmin(admin.ModelAdmin):
    list_display = ('produto', 'status_certificacao', 'data_envio', 'admin_responsavel')
    list_filter = ('status_certificacao',)
    
