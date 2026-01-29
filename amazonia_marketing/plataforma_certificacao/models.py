# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings


# ============================================================================
# MODELS DE AUTENTICAÇÃO E USUÁRIOS
# ============================================================================

class CustomUserManager(BaseUserManager):
    """Manager customizado para CustomUser - substitui o UserManager padrão do Django"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Cria e salva um usuário comum com email e senha"""
        if not email:
            raise ValueError('O usuário deve ter um endereço de email')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Cria e salva um superusuário com email e senha"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        """Permite autenticação por email"""
        return self.get(email=email)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário customizado para o sistema de certificação.
    Substitui o User padrão do Django e permite login com EMAIL.
    
    Tipos de usuário:
    - produtor: Cadastra produtos e solicita certificações
    - empresa: Compra produtos certificados (precisa verificação de CNPJ)
    - admin: Auditor que aprova/nega certificações e verifica empresas
    """
    TIPO_CHOICES = [
        ('produtor', 'Produtor'),
        ('empresa', 'Empresa'),
        ('admin', 'Administrador/Auditor'),
    ]
    
    id_usuario = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=100, unique=True, verbose_name='Email')
    nome = models.CharField(max_length=100, verbose_name='Nome Completo')
    tipo = models.CharField(max_length=8, choices=TIPO_CHOICES, default='produtor', verbose_name='Tipo de Usuário')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name='Endereço')
    
    # Campos obrigatórios do Django
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_staff = models.BooleanField(default=False, verbose_name='Membro da Equipe')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    
    objects = CustomUserManager()
    
    # Configuração de autenticação
    USERNAME_FIELD = 'email'  # Login com email
    REQUIRED_FIELDS = ['nome', 'tipo']  # Campos obrigatórios além de email e password
    
    class Meta:
        db_table = 'UsuarioBase'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
    
    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        return self.nome
    
    def get_short_name(self):
        """Retorna o nome curto do usuário"""
        return self.nome.split()[0] if self.nome else self.email


class Produtor(models.Model):
    """
    Model específica para produtores, com relação 1:1 com CustomUser.
    Contém informações específicas de produtores (rural ou urbano).
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='produtor_profile')
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text='Biografia do produtor')
    foto_perfil = models.ImageField(upload_to='perfis/produtores/', blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=100, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    class Meta:
        db_table = 'Produtores'
        verbose_name = 'Produtor'
        verbose_name_plural = 'Produtores'
    
    def __str__(self):
        return f"Produtor: {self.usuario.nome}"


class EmpresaProdutor(models.Model):
    """
    Model específica para empresas que compram produtos certificados.
    Empresas precisam de verificação de CNPJ e documentação pelo admin/auditor.
    Contém informações específicas de empresas compradoras.
    """
    STATUS_VERIFICACAO_CHOICES = [
        ('pendente', 'Pendente'),
        ('verificado', 'Verificado'),
        ('rejeitado', 'Rejeitado'),
    ]
    
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='empresa_profile')
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
    razao_social = models.CharField(max_length=255, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True)
    
    # Documentação obrigatória para verificação
    documento_contrato_social = models.FileField(upload_to='empresas/documentos/', blank=True, null=True, help_text='Contrato Social ou Estatuto')
    documento_cnpj = models.FileField(upload_to='empresas/documentos/', blank=True, null=True, help_text='Comprovante de CNPJ')
    documento_alvara = models.FileField(upload_to='empresas/documentos/', blank=True, null=True, help_text='Alvará de Funcionamento')
    
    # Status de verificação pelo admin/auditor
    status_verificacao = models.CharField(max_length=10, choices=STATUS_VERIFICACAO_CHOICES, default='pendente')
    data_verificacao = models.DateTimeField(blank=True, null=True)
    observacoes_verificacao = models.TextField(blank=True, null=True, help_text='Observações do auditor sobre a verificação')
    
    # Endereço comercial
    endereco_comercial = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    
    # Contato
    telefone_comercial = models.CharField(max_length=20, blank=True, null=True)
    site = models.URLField(blank=True, null=True)
    
    # Bio e mídia
    descricao_empresa = models.TextField(blank=True, null=True, help_text='Descrição da empresa')
    logo = models.ImageField(upload_to='perfis/empresas/', blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    class Meta:
        db_table = 'Empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return f"Empresa: {self.razao_social or self.usuario.nome}"


# ============================================================================
# MODELS PARA API DE EMPRESAS
# ============================================================================

# (from django.db import models) e (from django.contrib.auth.models import User) já foram importados acima
# Validador de CNPJ é importante para garantir que só números válidos entrem no banco
from django.core.validators import RegexValidator

class Empresa(models.Model):
    # --- Vínculo com o Usuário ---
    # Uma empresa pertence a um usuário (dono/representante)
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='empresa_perfil')

    # --- Dados da API (Receita Federal) ---
    cnpj = models.CharField(
        max_length=14, 
        unique=True,
        validators=[RegexValidator(r'^\d{14}$', 'O CNPJ deve ter 14 dígitos numéricos.')],
        help_text="Apenas números."
    )
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nome Fantasia")
    
    # Situação cadastral na Receita (ex: Ativa, Baixada). Importante para o Auditor.
    situacao_cadastral_receita = models.CharField(max_length=50, null=True, blank=True)
    data_abertura = models.DateField(null=True, blank=True)
    
    # Atividade principal (CNAE). Útil para filtrar empresas do setor "Marketing" ou "Agro".
    cnae_principal_descricao = models.CharField(max_length=255, null=True, blank=True, verbose_name="Atividade Principal")

    # --- Endereço (Vindo da API) ---
    logradouro = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True) # A API as vezes não traz número, o user completa
    municipio = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True) # Estado (PA, AM, etc)

    # --- Campos Internos do Amazônia Marketing ---
    
    # Documento para validação (ex: Contrato Social ou Cartão CNPJ em PDF/Imagem)
    documento_validacao = models.FileField(
        upload_to='documentos_empresas/', 
        verbose_name="Documento de Validação (PDF/Imagem)",
        help_text="Envie o Contrato Social ou Cartão CNPJ para auditoria."
    )

    # Status interno. É aqui que o seu Auditor trabalha.
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Aprovação'),
        ('APROVADO', 'Verificado e Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    ]
    status_auditoria = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDENTE'
    )

    # Selo de "Empresa Verificada" que aparecerá no site
    is_verified = models.BooleanField(default=False, verbose_name="Selo de Verificado")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nome_fantasia or self.razao_social} ({self.cnpj})"

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


# ============================================================================
# MODELS DE NEGÓCIO (Certificações, Produtos, Marketplace)
# ============================================================================

class Certificacoes(models.Model):
    """
    Model para gerenciar certificações de produtos.
    Armazena autodeclarações, documentos e status de certificação.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    
    id_certificacao = models.AutoField(primary_key=True)
    texto_autodeclaracao = models.TextField(blank=True, null=True)
    documento = models.FileField(upload_to='certificacoes/', max_length=255)
    documento_2 = models.FileField(upload_to='certificacoes/', max_length=255, blank=True, null=True)
    documento_3 = models.FileField(upload_to='certificacoes/', max_length=255, blank=True, null=True)
    status_certificacao = models.CharField(max_length=9, choices=STATUS_CHOICES, default='pendente', blank=True, null=True)
    data_envio = models.DateField(blank=True, null=True)
    data_resposta = models.DateField(blank=True, null=True)
    observacoes_admin = models.TextField(blank=True, null=True, help_text='Observações do auditor')
    produto = models.ForeignKey('Produtos', models.DO_NOTHING, db_column='produto_id')
    admin_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='admin_responsavel_id', blank=True, null=True)
    
    class Meta:
        db_table = 'Certificacoes'
        verbose_name = 'Certificação'
        verbose_name_plural = 'Certificações'
    
    def __str__(self):
        return f"Certificação {self.id_certificacao} - {self.produto.nome}"


class Marketplace(models.Model):
    """
    Model para gerenciar anúncios e conteúdo gerado para marketplaces.
    """
    id_anuncio = models.AutoField(primary_key=True)
    plataforma = models.CharField(max_length=80)
    conteudo_gerado = models.TextField(blank=True, null=True)
    data_geracao = models.DateField(blank=True, null=True)
    produto = models.ForeignKey('Produtos', models.DO_NOTHING, db_column='produto_id')

    class Meta:
        db_table = 'Marketplace'
        verbose_name = 'Anúncio Marketplace'
        verbose_name_plural = 'Anúncios Marketplace'
    
    def __str__(self):
        return f"Anúncio {self.id_anuncio} - {self.plataforma}"


class Produtos(models.Model):
    """
    Model para gerenciar produtos vendidos pelos usuários.
    """
    STATUS_ESTOQUE_CHOICES = [
        ('disponivel', 'Disponível'),
        ('esgotado', 'Esgotado'),
    ]
    
    id_produto = models.AutoField(primary_key=True)
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status_estoque = models.CharField(max_length=10, choices=STATUS_ESTOQUE_CHOICES, default='disponivel', blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='usuario_id')
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    
    class Meta:
        db_table = 'Produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
    
    def __str__(self):
        return self.nome


# ============================================================================
# MODELS LEGADAS (Mantidas para compatibilidade com dados existentes)
# ============================================================================

class UsuariosLegado(models.Model):
    """
    Model legada mantida para compatibilidade com dados existentes.
    Esta tabela está sendo gradualmente substituída por UsuarioBase, Produtor e Empresa.
    
    ⚠️ DESCONTINUADA: Use UsuarioBase, Produtor ou Empresa para novos registros.
    """
    TIPO_CHOICES = [
        ('produtor', 'Produtor'),
        ('empresa', 'Empresa'),
        ('admin', 'Admin'),
    ]
    
    id_usuario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    tipo = models.CharField(max_length=8, choices=TIPO_CHOICES)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    matricula = models.CharField(max_length=12, blank=True, null=True)

    class Meta:
        db_table = 'Usuarios'
        managed = False  # Tabela legada mantida para compatibilidade
        verbose_name = 'Usuário (Legado)'
        verbose_name_plural = 'Usuários (Legado)'
    
    def __str__(self):
        return f"{self.nome} ({self.tipo})"


# ============================================================================
# MODELS DE CARRINHO E CHECKOUT
# ============================================================================

class Carrinho(models.Model):
    """
    Model para gerenciar o carrinho de compras dos usuários.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carrinhos')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'Carrinho'
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
    
    def __str__(self):
        return f"Carrinho de {self.usuario.nome} - {self.data_criacao}"
    
    def get_total(self):
        """Calcula o total do carrinho"""
        total = sum(item.get_subtotal() for item in self.itens.all())
        return total
    
    def get_quantidade_itens(self):
        """Retorna a quantidade total de itens no carrinho"""
        return sum(item.quantidade for item in self.itens.all())


class ItemCarrinho(models.Model):
    """
    Model para itens individuais dentro do carrinho.
    """
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produtos, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    data_adicao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ItemCarrinho'
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = ['carrinho', 'produto']
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"
    
    def get_subtotal(self):
        """Calcula o subtotal do item"""
        return self.quantidade * self.preco_unitario


class Pedido(models.Model):
    """
    Model para gerenciar pedidos/compras realizadas.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODO_PAGAMENTO_CHOICES = [
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('mercado_pago', 'Mercado Pago'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Informações de pagamento
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, blank=True, null=True)
    id_transacao_pagamento = models.CharField(max_length=255, blank=True, null=True)
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    # Informações de entrega
    endereco_entrega = models.TextField()
    cidade_entrega = models.CharField(max_length=100)
    estado_entrega = models.CharField(max_length=2)
    cep_entrega = models.CharField(max_length=9)
    telefone_contato = models.CharField(max_length=20)
    
    # Observações
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'Pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']
    
    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario.nome} - {self.status}"


class ItemPedido(models.Model):
    """
    Model para itens individuais dentro do pedido.
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produtos, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'ItemPedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Pedido #{self.pedido.pk})"
