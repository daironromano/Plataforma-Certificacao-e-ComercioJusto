# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Certificacoes(models.Model):
    id_certificacao = models.AutoField(primary_key=True)
    texto_autodeclaracao = models.TextField(blank=True, null=True)
    documento = models.CharField(max_length=255)
    status_certificacao = models.CharField(max_length=9, blank=True, null=True)
    data_envio = models.DateField(blank=True, null=True)
    data_resposta = models.DateField(blank=True, null=True)
    produto = models.ForeignKey('Produtos', models.DO_NOTHING)
    admin_responsavel = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'certificacoes'


class Marketplace(models.Model):
    id_anuncio = models.AutoField(primary_key=True)
    plataforma = models.CharField(max_length=80)
    conteudo_gerado = models.TextField(blank=True, null=True)
    data_geracao = models.DateField(blank=True, null=True)
    produto = models.ForeignKey('Produtos', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'marketplace'


class Produtos(models.Model):
    id_produto = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status_estoque = models.CharField(max_length=10, blank=True, null=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'produtos'


class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    tipo = models.CharField(max_length=8)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    matricula = models.CharField(max_length=12, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'
