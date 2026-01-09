from django.contrib import admin
from .models import Produtos, Certificacoes, Marketplace, Usuarios


@admin.register(Produtos)
class ProdutosAdmin(admin.ModelAdmin):
    """Interface Django para gerenciar Produtos"""
    list_display = ('id_produto', 'nome', 'categoria', 'preco', 'status_estoque', 'usuario')
    list_filter = ('categoria', 'status_estoque', 'usuario')
    search_fields = ('nome', 'categoria', 'descricao')
    readonly_fields = ('id_produto',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_produto', 'nome', 'categoria')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'preco', 'status_estoque')
        }),
        ('Produtor', {
            'fields': ('usuario',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Se estiver editando um objeto existente
            return self.readonly_fields + ('usuario',)
        return self.readonly_fields


@admin.register(Certificacoes)
class CertificacoesAdmin(admin.ModelAdmin):
    """Interface Django para gerenciar Certificações"""
    list_display = ('id_certificacao', 'produto', 'status_certificacao', 'data_envio', 'data_resposta', 'admin_responsavel')
    list_filter = ('status_certificacao', 'data_envio', 'admin_responsavel')
    search_fields = ('produto__nome', 'documento')
    readonly_fields = ('id_certificacao', 'data_envio')
    date_hierarchy = 'data_envio'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_certificacao', 'produto', 'data_envio')
        }),
        ('Conteúdo', {
            'fields': ('texto_autodeclaracao', 'documento')
        }),
        ('Status e Resposta', {
            'fields': ('status_certificacao', 'data_resposta', 'admin_responsavel')
        }),
    )
    
    def get_queryset(self, request):
        """Filtrar certificações - admin vê todas, usuário vê só suas"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(admin_responsavel=request.user)
        return qs
    
    actions = ['marcar_aprovado', 'marcar_rejeitado']
    
    def marcar_aprovado(self, request, queryset):
        """Ação em massa para aprovar"""
        from django.utils.timezone import now
        updated = 0
        for cert in queryset.filter(status_certificacao='Pendente'):
            cert.status_certificacao = 'Aprovado'
            cert.admin_responsavel = request.user
            cert.data_resposta = now().date()
            cert.save()
            updated += 1
        self.message_user(request, f'{updated} certificação(ões) aprovada(s).')
    marcar_aprovado.short_description = "✓ Aprovar selecionadas"
    
    def marcar_rejeitado(self, request, queryset):
        """Ação em massa para rejeitar"""
        from django.utils.timezone import now
        updated = 0
        for cert in queryset.filter(status_certificacao='Pendente'):
            cert.status_certificacao = 'Rejeitado'
            cert.admin_responsavel = request.user
            cert.data_resposta = now().date()
            cert.save()
            updated += 1
        self.message_user(request, f'{updated} certificação(ões) rejeitada(s).', level='warning')
    marcar_rejeitado.short_description = "✗ Rejeitar selecionadas"


@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):
    """Interface Django para gerenciar Marketplace"""
    list_display = ('id_anuncio', 'produto', 'plataforma', 'data_geracao')
    list_filter = ('plataforma', 'data_geracao', 'produto__usuario')
    search_fields = ('produto__nome', 'plataforma', 'conteudo_gerado')
    readonly_fields = ('id_anuncio', 'data_geracao')
    date_hierarchy = 'data_geracao'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_anuncio', 'produto', 'plataforma')
        }),
        ('Conteúdo', {
            'fields': ('conteudo_gerado',)
        }),
        ('Data', {
            'fields': ('data_geracao',)
        }),
    )
    
    def get_queryset(self, request):
        """Filtrar anúncios - admin vê todos, usuário vê só seus"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(produto__usuario=request.user)
        return qs


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    """Interface Django para gerenciar Usuários"""
    list_display = ('id_usuario', 'nome', 'email', 'tipo', 'cpf', 'cnpj')
    list_filter = ('tipo',)
    search_fields = ('nome', 'email', 'cpf', 'cnpj')
    readonly_fields = ('id_usuario',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_usuario', 'nome', 'email', 'tipo')
        }),
        ('Contato', {
            'fields': ('telefone', 'endereco')
        }),
        ('Documentação', {
            'fields': ('cpf', 'cnpj', 'matricula')
        }),
        ('Segurança', {
            'fields': ('senha',)
        }),
    )

