from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Produtor, EmpresaProdutor, Certificacoes, Produtos


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
# ADMIN PARA EMPRESAS
# ============================================================================
from django.utils.html import format_html
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # --- 1. O que aparece na lista geral ---
    list_display = (
        'razao_social', 
        'cnpj', 
        'status_colorido',  # Nossa função visual customizada
        'is_verified', 
        'cnae_principal_descricao',
        'link_documento'    # Link rápido para o documento
    )
    
    # --- 2. Filtros Laterais (Facilita a vida do auditor) ---
    list_filter = ('status_auditoria', 'situacao_cadastral_receita', 'uf', 'is_verified')
    
    # --- 3. Barra de Pesquisa ---
    search_fields = ('razao_social', 'cnpj', 'usuario__email')

    # --- 4. Ações em Massa (Menu "Ação") ---
    actions = ['aprovar_empresas', 'rejeitar_empresas']

    # --- 5. Organização do Formulário de Edição ---
    fieldsets = (
        ('Dados de Auditoria (Área de Decisão)', {
            'fields': ('status_auditoria', 'is_verified', 'documento_validacao', 'link_documento_detalhe'),
            'description': 'Verifique o documento abaixo e altere o status.'
        }),
        ('Dados Oficiais (Vindos da API)', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'situacao_cadastral_receita', 
                       'cnae_principal_descricao', 'data_abertura'),
            'classes': ('collapse',), # Esconde essa área por padrão para limpar a tela
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'municipio', 'uf'),
            'classes': ('collapse',),
        }),
    )

    # --- 6. Campos que ninguém pode editar (Segurança) ---
    readonly_fields = (
        'razao_social', 'nome_fantasia', 'cnpj', 'situacao_cadastral_receita', 
        'cnae_principal_descricao', 'data_abertura', 'logradouro', 'numero', 
        'municipio', 'uf', 'link_documento_detalhe'
    )

    # --- Funções Customizadas ---

    def aprovar_empresas(self, request, queryset):
        # Atualiza status e marca o checkbox de verificado
        queryset.update(status_auditoria='APROVADO', is_verified=True)
        self.message_user(request, "Empresas aprovadas com sucesso e selo emitido!")
    aprovar_empresas.short_description = "Aprovar empresas selecionadas (Emitir Selo)"

    def rejeitar_empresas(self, request, queryset):
        # Atualiza status e remove o selo se existir
        queryset.update(status_auditoria='REJEITADO', is_verified=False)
        self.message_user(request, "Empresas rejeitadas.")
    rejeitar_empresas.short_description = "Rejeitar empresas selecionadas"

    # Cria uma "bolinha" colorida baseada no status
    def status_colorido(self, obj):
        colors = {
            'PENDENTE': 'orange',
            'APROVADO': 'green',
            'REJEITADO': 'red',
        }
        color = colors.get(obj.status_auditoria, 'black')
        # Retorna HTML seguro para o Django renderizar
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_auditoria_display()
        )
    status_colorido.short_description = 'Status Auditoria'

    # Link para abrir o arquivo na lista geral
    def link_documento(self, obj):
        if obj.documento_validacao:
            return format_html('<a href="{}" target="_blank">Abrir Arquivo</a>', obj.documento_validacao.url)
        return "-"
    link_documento.short_description = "Documento"

    # Visualização do documento dentro do formulário detalhado
    def link_documento_detalhe(self, obj):
        if obj.documento_validacao:
            # Se for imagem, mostra um preview pequeno
            if obj.documento_validacao.url.lower().endswith(('.png', '.jpg', '.jpeg')):
                return format_html(
                    '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px;"/></a><br><a href="{0}" target="_blank">Ver Imagem Completa</a>',
                    obj.documento_validacao.url
                )
            # Se for PDF ou outro, mostra botão
            return format_html('<a class="button" href="{}" target="_blank">Baixar/Visualizar Documento</a>', obj.documento_validacao.url)
        return "Nenhum documento enviado."
    link_documento_detalhe.short_description = "Visualização do Documento"



# ============================================================================
# ADMIN PARA USUÁRIOS
# ============================================================================

# Essa configuração permite que os campos de usuário sejam mostrados
# na tabela usuários ao criar um cadastro.
# ============================================================================
# ADMIN PARA CUSTOM USER (AUTH_USER_MODEL)
# ============================================================================

# CustomUserAdmin - Gerencia o modelo de autenticação customizado
class CustomUserAdmin(UserAdmin):
    """
    Admin para CustomUser (modelo AUTH_USER_MODEL).
    Permite gerenciar usuários do sistema: Produtores, Empresas e Admins/Auditores.
    Login com EMAIL.
    """
    model = CustomUser
    list_display = ('email', 'nome', 'tipo', 'is_active', 'is_staff', 'data_criacao')
    list_filter = ('tipo', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome', 'tipo', 'telefone', 'endereco')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'data_criacao', 'data_atualizacao')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'tipo', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
    
    readonly_fields = ('data_criacao', 'data_atualizacao', 'last_login')

# Registra o usuário customizado
admin.site.register(CustomUser, CustomUserAdmin)


# ============================================================================
# ADMIN PARA PERFIS (PRODUTOR E EMPRESA)
# ============================================================================

@admin.register(Produtor)
class ProdutorAdmin(admin.ModelAdmin):
    """Admin para perfis de Produtores"""
    list_display = ('get_nome', 'get_email', 'cpf', 'cidade', 'estado', 'data_criacao')
    list_filter = ('estado', 'data_criacao')
    search_fields = ('usuario__nome', 'usuario__email', 'cpf', 'cidade')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    
    def get_nome(self, obj):
        return obj.usuario.nome
    get_nome.short_description = 'Nome'
    get_nome.admin_order_field = 'usuario__nome'
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'usuario__email'

@admin.register(EmpresaProdutor)
class EmpresaProdutorAdmin(admin.ModelAdmin):
    """Admin para perfis de Empresas Compradoras"""
    list_display = ('get_nome', 'get_email', 'cnpj', 'razao_social', 'status_verificacao', 'data_verificacao')
    list_filter = ('status_verificacao', 'estado', 'data_verificacao')
    search_fields = ('usuario__nome', 'usuario__email', 'cnpj', 'razao_social', 'nome_fantasia')
    readonly_fields = ('data_verificacao',)
    
    fieldsets = (
        ('Usuário', {'fields': ('usuario',)}),
        ('Dados da Empresa', {'fields': ('cnpj', 'razao_social', 'nome_fantasia', 'inscricao_estadual')}),
        ('Documentação', {'fields': ('documento_contrato_social', 'documento_cnpj', 'documento_alvara')}),
        ('Verificação pelo Auditor', {'fields': ('status_verificacao', 'data_verificacao', 'observacoes_verificacao')}),
        ('Endereço', {'fields': ('endereco_comercial', 'cidade', 'estado', 'cep')}),
    )
    
    def get_nome(self, obj):
        return obj.usuario.nome
    get_nome.short_description = 'Nome'
    get_nome.admin_order_field = 'usuario__nome'
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'usuario__email'


# ============================================================================
# ADMIN PARA NEGÓCIO
# ============================================================================

# Registros para os modelos de negócio
@admin.register(Certificacoes)
class CertificacoesAdmin(admin.ModelAdmin):
    list_display = ('id_certificacao', 'produto', 'status_certificacao', 'data_envio', 'admin_responsavel')
    list_filter = ('status_certificacao', 'data_envio')
    search_fields = ('produto__nome', 'admin_responsavel__username')
    readonly_fields = ('id_certificacao', 'data_envio', 'data_resposta')
    fieldsets = (
        ('Produto', {
            'fields': ('produto',)
        }),
        ('Documentação', {
            'fields': ('texto_autodeclaracao', 'arquivo_autodeclaracao')
        }),
        ('Status e Datas', {
            'fields': ('status_certificacao', 'data_envio', 'data_resposta')
        }),
        ('Responsável', {
            'fields': ('admin_responsavel',)
        }),
    )


@admin.register(Produtos)
class ProdutosAdmin(admin.ModelAdmin):
    list_display = ('id_produto', 'nome', 'status_estoque', 'preco', 'usuario')
    list_filter = ('status_estoque',)
    search_fields = ('nome', 'usuario__nome')
    readonly_fields = ('id_produto',)
    fieldsets = (
        ('Identificação', {
            'fields': ('nome',)
        }),
        ('Descrição e Imagem', {
            'fields': ('descricao', 'imagem')
        }),
        ('Informações Comerciais', {
            'fields': ('preco', 'status_estoque')
        }),
        ('Propriedade', {
            'fields': ('usuario',)
        }),
    )

    
