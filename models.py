from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# 1. GESTÃO DE USUÁRIOS (Personas)
# Baseado na definição de perfis: Produtores Rurais, Empresas e Admins[cite: 14].
class User(AbstractUser):
    class Types(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador/Auditor'
        PRODUTOR = 'PRODUTOR', 'Produtor Rural'
        EMPRESA = 'EMPRESA', 'Empresa (PME)'

    type = models.CharField(
        max_length=50, 
        choices=Types.choices, 
        default=Types.PRODUTOR, 
        verbose_name="Tipo de Usuário"
    )

    # Identificação única para empresas e produtores [cite: 31]
    document_id = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="CPF ou CNPJ"
    ) 

# Perfil estendido para informações específicas do negócio
class ProducerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(verbose_name="Endereço Completo") [cite: 31]
    
    # "Escrita do Diferencial" solicitado na reunião 
    differential = models.TextField(
        verbose_name="Diferencial do Produtor", 
        help_text="Descreva o que torna seus produtos únicos."
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.user.document_id}"

# 2. MAPEAMENTO E PRODUTOS
# Categorização para organização na plataforma [cite: 36]
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    # Status logísticos definidos na ata 
    class StockStatus(models.TextChoices):
        EM_ESTOQUE = 'EM_ESTOQUE', 'Em Estoque'
        DISPONIVEL = 'DISPONIVEL', 'Disponível para Encomenda'
        ESGOTADO = 'ESGOTADO', 'Esgotado'

    producer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, verbose_name="Nome do Produto")
    description = models.TextField(verbose_name="Descrição Detalhada")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    
    # Controle Logístico 
    stock_status = models.CharField(
        max_length=20, 
        choices=StockStatus.choices, 
        default=StockStatus.EM_ESTOQUE
    )

    # Integração Futura com Marketplaces (Mercado Livre) [cite: 44]
    # Armazena o ID do anúncio externo para evitar duplicação
    mercadolivre_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# 3. PROTOCOLO DE CERTIFICAÇÃO (Selo de Qualidade)
# Focado na autodeclaração e validação pelo Admin [cite: 23, 24]
class Certification(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente de Análise'
        APPROVED = 'APPROVED', 'Aprovado (Selo Ativo)'
        REJECTED = 'REJECTED', 'Reprovado'

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='certification')
    
    # Documentação exigida para autodeclaração 
    tech_sheet = models.FileField(upload_to='docs/tech_sheets/', verbose_name="Ficha Técnica")
    invoice = models.FileField(upload_to='docs/invoices/', verbose_name="Nota Fiscal")
    photo_evidence = models.ImageField(upload_to='docs/photos/', verbose_name="Foto do Produto/Produção")

    # Auditoria 
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    auditor_notes = models.TextField(blank=True, verbose_name="Notas do Auditor (Motivo de Reprovação)")
    validated_at = models.DateTimeField(null=True, blank=True)
    
    # Quem aprovou (Admin)
    validated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'type': User.Types.ADMIN},
        related_name='audits'
    )

    def __str__(self):
        return f"Certificação: {self.product.name} - {self.status}"

# 4. FEEDBACK E REPUTAÇÃO
# Registro de feedbacks de vendas passadas [cite: 34]
class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feedbacks')
    buyer_name = models.CharField(max_length=100) # Pode ser anônimo ou usuário do sistema
    comment = models.TextField()
    rating = models.PositiveIntegerField(default=5) # Escala de 1 a 5
    created_at = models.DateTimeField(auto_now_add=True)