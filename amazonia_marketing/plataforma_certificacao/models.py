# Django Models - Sistema de Certificação e Comércio Justo
# Arquitetura: Herança Multi-Tabela com UsuarioBase como base
# Padrão: Cada tipo de usuário (Produtor, Empresa, Admin) herda de UsuarioBase

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator


# ============================================================================
# MANAGERS CUSTOMIZADOS
# ============================================================================

class UsuarioBaseManager(BaseUserManager):
    """Manager customizado para usuários"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Cria um usuário comum"""
        if not email:
            raise ValueError('O usuário deve ter um endereço de email')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Cria um superusuário"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        """Permite autenticação por email"""
        return self.get(email=email)

    def produtores(self):
        """Retorna todos os produtores ativos"""
        return self.filter(tipo='produtor', is_active=True)
    
    def empresas(self):
        """Retorna todas as empresas ativas"""
        return self.filter(tipo='empresa', is_active=True)
    
    def admins(self):
        """Retorna todos os auditores/admins ativos"""
        return self.filter(tipo='admin', is_active=True)


# ============================================================================
# MODELO BASE DE AUTENTICAÇÃO
# ============================================================================

class UsuarioBase(AbstractBaseUser, PermissionsMixin):
    """
    Modelo base para todos os usuários do sistema.
    Substitui o User padrão do Django e permite login com EMAIL.
    
    ARQUITETURA: Classe pai na herança multi-tabela.
    Todos os usuários especializados (Produtor, Empresa, Admin) relacionam-se com esta classe via OneToOneField.
    
    Tipos: produtor, empresa, admin
    """
    TIPO_CHOICES = [
        ('produtor', 'Produtor'),
        ('empresa', 'Empresa'),
        ('admin', 'Administrador/Auditor'),
    ]
    
    id_usuario = models.AutoField(primary_key=True)
    email = models.EmailField(
        max_length=100, 
        unique=True, 
        verbose_name='Email',
        validators=[EmailValidator()],
    )
    nome = models.CharField(
        max_length=100, 
        verbose_name='Nome Completo',
    )
    tipo = models.CharField(
        max_length=8, 
        choices=TIPO_CHOICES, 
        default='produtor', 
        verbose_name='Tipo de Usuário',
    )
    
    telefone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='Telefone',
    )
    endereco = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Endereço',
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_staff = models.BooleanField(default=False, verbose_name='Membro da Equipe')
    is_superuser = models.BooleanField(default=False, verbose_name='Superusuário')
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    
    objects = UsuarioBaseManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'tipo']
    
    class Meta:
        db_table = 'UsuarioBase'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['tipo', 'is_active']),
            models.Index(fields=['data_criacao']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
    
    def get_full_name(self):
        return self.nome
    
    def get_short_name(self):
        return self.nome.split()[0] if self.nome else self.email
    
    def is_produtor(self):
        return self.tipo == 'produtor'
    
    def is_empresa(self):
        return self.tipo == 'empresa'
    
    def is_admin_auditor(self):
        return self.tipo == 'admin'


# ============================================================================
# MODELOS ESPECIALIZADOS - PERFIS DE USUÁRIO
# ============================================================================

class ProdutorProfile(models.Model):
    """
    Perfil especializado para produtores (herança 1:1 com UsuarioBase).
    Informações específicas: CPF, localização, redes sociais.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='produtor_profile',
        limit_choices_to={'tipo': 'produtor'},
    )
    
    cpf = models.CharField(
        max_length=14, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name='CPF',
    )
    
    bio = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Biografia',
    )
    foto_perfil = models.ImageField(
        upload_to='perfis/produtores/',
        blank=True, 
        null=True,
        verbose_name='Foto de Perfil',
    )
    
    cidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Cidade'
    )
    estado = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        verbose_name='Estado (UF)',
    )
    cep = models.CharField(
        max_length=9, 
        blank=True, 
        null=True,
        verbose_name='CEP'
    )
    
    whatsapp = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='WhatsApp',
    )
    instagram = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Instagram',
    )
    facebook = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Facebook',
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'ProdutorProfile'
        verbose_name = 'Perfil de Produtor'
        verbose_name_plural = 'Perfis de Produtores'
    
    def __str__(self):
        return f"Perfil: {self.usuario.nome}"
    
    def get_localizacao(self):
        """Retorna a localização formatada"""
        if self.cidade and self.estado:
            return f"{self.cidade}, {self.estado}"
        return "Localização não informada"


# Compatibilidade
Produtor = ProdutorProfile


class EmpresaProfile(models.Model):
    """
    Perfil especializado para empresas (herança 1:1 com UsuarioBase).
    Informações: CNPJ, documentação, verificação.
    """
    STATUS_VERIFICACAO_CHOICES = [
        ('pendente', 'Pendente de Verificação'),
        ('verificado', 'Verificado e Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('suspenso', 'Suspenso'),
    ]
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='empresa_profile',
        limit_choices_to={'tipo': 'empresa'},
    )
    
    cnpj = models.CharField(
        max_length=18, 
        blank=True, 
        null=True,
        verbose_name='CNPJ',
    )
    razao_social = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Razão Social',
    )
    nome_fantasia = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Nome Fantasia',
    )
    inscricao_estadual = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Inscrição Estadual'
    )
    
    documento_contrato_social = models.FileField(
        upload_to='empresas/documentos/',
        blank=True, 
        null=True,
        verbose_name='Contrato Social',
    )
    documento_cnpj = models.FileField(
        upload_to='empresas/documentos/',
        blank=True, 
        null=True,
        verbose_name='Comprovante de CNPJ',
    )
    documento_alvara = models.FileField(
        upload_to='empresas/documentos/',
        blank=True, 
        null=True,
        verbose_name='Alvará de Funcionamento',
    )
    
    status_verificacao = models.CharField(
        max_length=10, 
        choices=STATUS_VERIFICACAO_CHOICES, 
        default='pendente',
        verbose_name='Status de Verificação'
    )
    data_verificacao = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='Data da Verificação',
    )
    observacoes_verificacao = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Observações do Auditor',
    )
    admin_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='empresas_verificadas',
        verbose_name='Auditor Responsável',
    )
    
    endereco_comercial = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Endereço Comercial'
    )
    cidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Cidade'
    )
    estado = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        verbose_name='Estado (UF)'
    )
    cep = models.CharField(
        max_length=9, 
        blank=True, 
        null=True,
        verbose_name='CEP'
    )
    
    telefone_comercial = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Telefone Comercial'
    )
    site = models.URLField(
        blank=True, 
        null=True,
        verbose_name='Website',
    )
    
    descricao_empresa = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Descrição da Empresa',
    )
    logo = models.ImageField(
        upload_to='perfis/empresas/',
        blank=True, 
        null=True,
        verbose_name='Logo',
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'EmpresaProfile'
        verbose_name = 'Perfil de Empresa'
        verbose_name_plural = 'Perfis de Empresas'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['status_verificacao']),
        ]
    
    def __str__(self):
        return f"Empresa: {self.razao_social or self.usuario.nome}"
    
    def get_nome_exibicao(self):
        return self.nome_fantasia or self.razao_social or self.usuario.nome
    
    def is_verificada(self):
        return self.status_verificacao == 'verificado'
    
    def pode_comprar(self):
        return self.is_verificada() and self.usuario.is_active


# Compatibilidade
EmpresaProdutor = EmpresaProfile


class AdminAuditorProfile(models.Model):
    """
    Perfil especializado para administradores/auditores.
    Informações: matricula, departamento, permissões.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        limit_choices_to={'tipo': 'admin'},
    )
    
    matricula = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Matrícula',
    )
    departamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Departamento',
    )
    
    pode_auditar_produtores = models.BooleanField(
        default=True,
        verbose_name='Pode Auditar Produtores',
    )
    pode_verificar_empresas = models.BooleanField(
        default=True,
        verbose_name='Pode Verificar Empresas',
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    ultimo_acesso = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Último Acesso',
    )
    
    class Meta:
        db_table = 'AdminAuditorProfile'
        verbose_name = 'Perfil de Admin/Auditor'
        verbose_name_plural = 'Perfis de Admins/Auditores'
    
    def __str__(self):
        return f"Admin: {self.usuario.nome} ({self.matricula})"
    
    def registrar_ultimo_acesso(self):
        """Atualiza o timestamp do último acesso"""
        from django.utils import timezone
        self.ultimo_acesso = timezone.now()
        self.save(update_fields=['ultimo_acesso'])


# ============================================================================
# MODELS DE NEGÓCIO
# ============================================================================

class Produtos(models.Model):
    """
    Produtos cadastrados pelos produtores.
    Cada produto pode ter múltiplas certificações.
    """
    STATUS_ESTOQUE_CHOICES = [
        ('disponivel', 'Disponível'),
        ('esgotado', 'Esgotado'),
    ]
    
    id_produto = models.AutoField(primary_key=True)
    
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Produto',
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição',
    )
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Preço Unitário',
    )
    
    status_estoque = models.CharField(
        max_length=10,
        choices=STATUS_ESTOQUE_CHOICES,
        default='disponivel',
        blank=True,
        null=True,
        verbose_name='Status de Estoque'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='usuario_id',
        related_name='produtos',
        verbose_name='Produtor',
    )
    imagem = models.ImageField(
        upload_to='produtos/',
        blank=True,
        null=True,
        verbose_name='Imagem',
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
        blank=True,
        null=True
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'Produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['status_estoque']),
        ]
    
    def __str__(self):
        return self.nome
    
    def tem_certificacao_aprovada(self):
        return self.certificacoes.filter(status_certificacao='aprovado').exists()
    
    def get_certificacoes_pendentes(self):
        return self.certificacoes.filter(status_certificacao='pendente')
    
    def get_certificacoes_aprovadas(self):
        return self.certificacoes.filter(status_certificacao='aprovado')


class Certificacoes(models.Model):
    """
    Certificações de produtos.
    Fluxo: Produtor envia -> Admin analisa -> Aprovado/Reprovado
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Análise'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    
    id_certificacao = models.AutoField(primary_key=True)
    
    produto = models.ForeignKey(
        'Produtos', 
        on_delete=models.CASCADE,
        related_name='certificacoes',
        verbose_name='Produto',
    )
    
    texto_autodeclaracao = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Texto da Autodeclaração',
    )
    
    documento = models.FileField(
        upload_to='certificacoes/',
        max_length=255,
        verbose_name='Documento Principal',
    )
    documento_2 = models.FileField(
        upload_to='certificacoes/',
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Documento Adicional 1'
    )
    documento_3 = models.FileField(
        upload_to='certificacoes/',
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Documento Adicional 2'
    )
    
    status_certificacao = models.CharField(
        max_length=9,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status',
        blank=True,
        null=True
    )
    
    data_envio = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Envio',
    )
    data_resposta = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Resposta',
    )
    
    observacoes_admin = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações do Auditor',
    )
    
    admin_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column='admin_responsavel_id',
        blank=True,
        null=True,
        related_name='certificacoes_analisadas',
        verbose_name='Auditor Responsável',
    )
    
    class Meta:
        db_table = 'Certificacoes'
        verbose_name = 'Certificação'
        verbose_name_plural = 'Certificações'
        ordering = ['-data_envio']
        indexes = [
            models.Index(fields=['status_certificacao']),
            models.Index(fields=['data_envio']),
            models.Index(fields=['produto', 'status_certificacao']),
        ]
    
    def __str__(self):
        return f"Certificação {self.id_certificacao} - {self.produto.nome}"
    
    def is_pendente(self):
        return self.status_certificacao == 'pendente'
    
    def is_aprovada(self):
        return self.status_certificacao == 'aprovado'
    
    def is_reprovada(self):
        return self.status_certificacao == 'reprovado'


class Marketplace(models.Model):
    """
    Anúncios para marketplaces externos.
    """
    id_anuncio = models.AutoField(primary_key=True)
    plataforma = models.CharField(max_length=80)
    conteudo_gerado = models.TextField(blank=True, null=True)
    data_geracao = models.DateField(blank=True, null=True)
    produto = models.ForeignKey('Produtos', on_delete=models.CASCADE, db_column='produto_id', related_name='anuncios')

    class Meta:
        db_table = 'Marketplace'
        verbose_name = 'Anúncio Marketplace'
        verbose_name_plural = 'Anúncios Marketplace'
    
    def __str__(self):
        return f"Anúncio {self.id_anuncio} - {self.plataforma}"


# ============================================================================
# MODELS DE CARRINHO E PEDIDOS
# ============================================================================

class Carrinho(models.Model):
    """
    Carrinho de compras dos usuários (empresas).
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrinhos',
        verbose_name='Usuário'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'Carrinho'
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
    
    def __str__(self):
        return f"Carrinho de {self.usuario.nome}"
    
    def get_total(self):
        """Calcula o total do carrinho"""
        return sum(item.get_subtotal() for item in self.itens.all())
    
    def get_quantidade_itens(self):
        """Retorna a quantidade total de itens"""
        return sum(item.quantidade for item in self.itens.all())


class ItemCarrinho(models.Model):
    """
    Itens dentro do carrinho.
    """
    carrinho = models.ForeignKey(
        Carrinho,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Carrinho'
    )
    produto = models.ForeignKey(
        Produtos,
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
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
    Pedidos realizados pelas empresas.
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
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name='Usuário'
    )
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    metodo_pagamento = models.CharField(
        max_length=20,
        choices=METODO_PAGAMENTO_CHOICES,
        blank=True,
        null=True
    )
    id_transacao_pagamento = models.CharField(max_length=255, blank=True, null=True)
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    endereco_entrega = models.TextField()
    cidade_entrega = models.CharField(max_length=100)
    estado_entrega = models.CharField(max_length=2)
    cep_entrega = models.CharField(max_length=9)
    telefone_contato = models.CharField(max_length=20)
    
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'Pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']
    
    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario.nome}"


class ItemPedido(models.Model):
    """
    Itens dentro do pedido.
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido'
    )
    produto = models.ForeignKey(
        Produtos,
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'ItemPedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
    
    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


# ============================================================================
# MODELS LEGADAS (compatibilidade)
# ============================================================================

class UsuariosLegado(models.Model):
    """
    Model legada para compatibilidade com dados existentes.
    ⚠️ DESCONTINUADA: Use UsuarioBase para novos registros.
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
        managed = False
        verbose_name = 'Usuário (Legado)'
        verbose_name_plural = 'Usuários (Legado)'
    
    def __str__(self):
        return f"{self.nome} ({self.tipo})"
