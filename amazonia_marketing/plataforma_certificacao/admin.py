from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin
from django.utils.html import format_html
from .models import (
    UsuarioBase, ProdutorProfile, EmpresaProfile, AdminAuditorProfile,
    Certificacoes, Produtos, Carrinho, ItemCarrinho, Pedido, ItemPedido,
    Marketplace, UsuariosLegado
)


# ============================================================================
# CONFIGURAÇÃO DE GRUPOS (Segurança e Permissões)
# ============================================================================

class CustomGroupAdmin(BaseGroupAdmin):
    """Customização para admin de grupos com melhor interface."""
    list_display = ('name', 'permissions_count')
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = 'Quantidade de Permissões'


# Re-registrar Group com customizações
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

admin.site.register(Group, CustomGroupAdmin)


# ============================================================================
# ADMIN PARA USUÁRIOS CUSTOMIZADOS
# ============================================================================

@admin.register(UsuarioBase)
class UsuarioBaseAdmin(UserAdmin):
    """Admin customizado para UsuarioBase"""
    list_display = ('email', 'nome', 'tipo', 'is_active', 'data_criacao')
    list_filter = ('tipo', 'is_active', 'data_criacao')
    search_fields = ('email', 'nome')
    ordering = ('-data_criacao',)
    
    fieldsets = (
        ('Autenticação', {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome', 'tipo', 'telefone', 'endereco')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Data', {'fields': ('data_criacao', 'data_atualizacao')}),
    )
    
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'nome', 'tipo', 'password1', 'password2')}),
    )


# ============================================================================
# ADMIN PARA PERFIS ESPECIALIZADOS
# ============================================================================

@admin.register(ProdutorProfile)
class ProdutorProfileAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cpf', 'cidade', 'estado', 'data_criacao')
    list_filter = ('estado', 'data_criacao')
    search_fields = ('usuario__nome', 'cpf')
    readonly_fields = ('data_criacao', 'data_atualizacao')


@admin.register(EmpresaProfile)
class EmpresaProfileAdmin(admin.ModelAdmin):
    list_display = ('get_razao_social', 'cnpj', 'status_verificacao', 'get_usuario_email')
    list_filter = ('status_verificacao', 'data_criacao')
    search_fields = ('usuario__nome', 'cnpj', 'razao_social')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    
    fieldsets = (
        ('Dados Básicos', {'fields': ('usuario', 'cnpj', 'razao_social', 'nome_fantasia', 'inscricao_estadual')}),
        ('Documentação', {'fields': ('documento_contrato_social', 'documento_cnpj', 'documento_alvara')}),
        ('Verificação', {'fields': ('status_verificacao', 'data_verificacao', 'observacoes_verificacao', 'admin_responsavel')}),
        ('Endereço', {'fields': ('endereco_comercial', 'cidade', 'estado', 'cep')}),
        ('Contato', {'fields': ('telefone_comercial', 'site')}),
        ('Descrição', {'fields': ('descricao_empresa', 'logo')}),
        ('Datas', {'fields': ('data_criacao', 'data_atualizacao')}),
    )
    
    def get_razao_social(self, obj):
        return obj.razao_social or obj.usuario.nome
    get_razao_social.short_description = 'Razão Social'
    
    def get_usuario_email(self, obj):
        return obj.usuario.email
    get_usuario_email.short_description = 'Email'


@admin.register(AdminAuditorProfile)
class AdminAuditorProfileAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'matricula', 'departamento', 'pode_auditar_produtores', 'pode_verificar_empresas')
    list_filter = ('pode_auditar_produtores', 'pode_verificar_empresas', 'data_criacao')
    search_fields = ('usuario__nome', 'matricula')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'ultimo_acesso')


# ============================================================================
# ADMIN PARA CERTIFICAÇÕES E PRODUTOS
# ============================================================================

@admin.register(Certificacoes)
class CertificacoesAdmin(admin.ModelAdmin):
    list_display = ('id_certificacao', 'produto', 'status_certificacao', 'data_envio', 'admin_responsavel')
    list_filter = ('status_certificacao', 'data_envio')
    search_fields = ('produto__nome', 'id_certificacao')
    readonly_fields = ('data_envio', 'data_resposta')
    
    fieldsets = (
        ('Produto', {'fields': ('produto',)}),
        ('Autodeclaração', {'fields': ('texto_autodeclaracao',)}),
        ('Documentos', {'fields': ('documento', 'documento_2', 'documento_3')}),
        ('Análise', {'fields': ('status_certificacao', 'observacoes_admin', 'admin_responsavel')}),
        ('Datas', {'fields': ('data_envio', 'data_resposta')}),
    )


@admin.register(Produtos)
class ProdutosAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'preco', 'status_estoque', 'data_criacao')
    list_filter = ('status_estoque', 'data_criacao')
    search_fields = ('nome', 'usuario__nome')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    
    fieldsets = (
        ('Informações Básicas', {'fields': ('nome', 'descricao', 'usuario')}),
        ('Preço e Estoque', {'fields': ('preco', 'status_estoque')}),
        ('Imagem', {'fields': ('imagem',)}),
        ('Datas', {'fields': ('data_criacao', 'data_atualizacao')}),
    )


# ============================================================================
# ADMIN PARA CARRINHO E PEDIDOS
# ============================================================================

class ItemCarrinhoInline(admin.TabularInline):
    """Inline para itens do carrinho"""
    model = ItemCarrinho
    extra = 0


@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'ativo', 'total_itens', 'data_atualizacao')
    list_filter = ('ativo', 'data_criacao')
    search_fields = ('usuario__nome', 'usuario__email')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    inlines = [ItemCarrinhoInline]
    
    def total_itens(self, obj):
        return obj.itens.count()
    total_itens.short_description = 'Quantidade de Itens'


class ItemPedidoInline(admin.TabularInline):
    """Inline para itens do pedido"""
    model = ItemPedido
    extra = 0
    readonly_fields = ('preco_unitario',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('pk', 'usuario', 'data_pedido', 'total', 'status')
    list_filter = ('status', 'data_pedido')
    search_fields = ('usuario__nome', 'usuario__email')
    readonly_fields = ('data_pedido', 'id_transacao_pagamento')
    inlines = [ItemPedidoInline]
    
    fieldsets = (
        ('Informações do Pedido', {'fields': ('usuario', 'status', 'total')}),
        ('Pagamento', {'fields': ('metodo_pagamento', 'id_transacao_pagamento', 'data_pagamento')}),
        ('Entrega', {'fields': ('endereco_entrega', 'cidade_entrega', 'estado_entrega', 'cep_entrega', 'telefone_contato')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Datas', {'fields': ('data_pedido',)}),
    )


# ============================================================================
# ADMIN PARA MARKETPLACE E USUÁRIOS LEGADO
# ============================================================================

@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):
    list_display = ('id_anuncio', 'produto', 'plataforma', 'data_geracao')
    list_filter = ('plataforma',)
    search_fields = ('produto__nome',)
    readonly_fields = ('id_anuncio',)
    
    fieldsets = (
        ('Produto', {'fields': ('produto', 'plataforma')}),
        ('Conteúdo', {'fields': ('conteudo_gerado',)}),
        ('Data', {'fields': ('data_geracao',)}),
    )


@admin.register(UsuariosLegado)
class UsuariosLegadoAdmin(admin.ModelAdmin):
    """Admin para usuários legado (compatibilidade)"""
    list_display = ('id_usuario', 'nome', 'email', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome', 'email')
    readonly_fields = ('id_usuario',)
    
    fieldsets = (
        ('Informações Básicas', {'fields': ('id_usuario', 'nome', 'email', 'tipo')}),
        ('Contato', {'fields': ('telefone', 'endereco')}),
        ('Documentos', {'fields': ('cpf', 'cnpj', 'matricula')}),
    )
    
    def has_add_permission(self, request):
        """Desabilita adição de novos usuários legado"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Desabilita exclusão de usuários legado"""
        return False

