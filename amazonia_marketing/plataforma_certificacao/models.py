# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser

# ==============================================================================
# REESTRUTURAÇÃO DO BANCO DE DADOS 
# ==============================================================================

# Usuário PAI (MELHORIA IMPLEMENTADA)

class CustomUser(AbstractUser):
    """
    Essa classe substitui o usuário padrão do Django. Ela herda campos como:
    username, password, email, first_name.
    Adicionamos apenas o campo para saber se é produtor, empresa ou admin.
    """
    
    # Definindo opções para o menu de escolhas (tupla de tuplas)
    TIPO_CHOICES = (
        ('produtor', 'Produtor'),
        ('empresa', 'Comprador'),
        ('auditor', 'Auditor'),
    )
    
    # Campo que vai guardar o tipo do usuário no banco de dados
    tipo_usuario = models.CharField(max_length=20,choices=TIPO_CHOICES,default='produtor')
    
    # --- Configurações técnicas obrigatórias --- 
    
    groups = models.ManyToManyField('auth.Group', related_name='costumuser_set', blank=True, verbose_name='groups', help_text='O grupo ao qual esse usuário pertence',)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='costumuser_set', blank=True, verbose_name='user permission', help_text='Permissão específica para esse usuário' )
    
    # Perfís específicos
    
class PerfilProduto(models.Model):
    # Relacionamento 1 para 1, ou seja, cada usuário tem apenas um perfil de produtor.
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='produtor_perfil')
    
    cpf = models.CharField(max_length=11, unique=True)
    nome = models.CharField(max_length=100)
    endereco = models.TextField()
    telefon = models.CharField(max_length=10)
    bio = models.TextField(blank=True, help_text='Breve descrição sobre o produtor')
    
    def __str__(self):
        return f'Perfil produtor: {self.user.username}'
    
class PerfilEmpresa(models.Model):
    # Relacionamento 1 para 1, ou seja, cada usuário tem apenas um perfil de empresa.
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='empresa_perfil')
    
    cnpj = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=100)
    
    # Arquivo para comprovar que é uma empresa legalizada
    
    def __str__(self):
        return f'Perfil empresa: {self.user.username}'
    
class Produtos(models.Model):
    # Chave primária 
    id_produto = models.AutoField(primary_key=True)
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    
    # Utilizando choices para evitar error de digitação
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('esgotado', 'Esgotado'),
        ('em_estoque', 'Em Estoque')
    )
    
    status_estoque = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponveil')
    
    # ALTERAÇÃO: LIGA AO CUSTOMUSER AGORA.
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nome   

class Certificacoes(models.Model):
    # Chave estrangeira
    id_certificacao = models.AutoField(primary_key=True)
    
    # Liga uma certificação a um produto. se deletado, deleta tudo em cascata.
    produto = models.ForeignKey(Produtos, on_delete=models.CASCADE)
    texto_autodeclaracao = models.TextField(blank=True, null=True)
    arquivo_autodeclaracao = models.FileField(upload_to='certificacoes/', blank=True, null=True)
    
    STATUS_CERT_CHOICES = (
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    )
    
    status_certificacao = models.CharField(max_length=9, choices=STATUS_CERT_CHOICES, default='pendente')
    data_envio = models.DateField(blank=True, null=True)
    data_resposta = models.DateField(blank=True, null=True)
    admin_responsavel = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='certificacoes_auditadas')
    
    
# =========================================================
# IMPLEMENTAÇÃO FUTURA
# =========================================================
# class Marketplace(models.Model):
#    id_anuncio = models.AutoField(primary_key=True)
#     plataforma = models.CharField(max_length=80)
#    conteudo_gerado = models.TextField(blank=True, null=True)
#     data_geracao = models.DateField(blank=True, null=True)
#     produto = models.ForeignKey('Produtos', models.DO_NOTHING)