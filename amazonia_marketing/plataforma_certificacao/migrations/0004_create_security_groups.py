"""
Migration para criar grupos de segurança padrão.
Grupos: Produtor, Empresa, Auditor (Admin)
"""

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from plataforma_certificacao.models import Produtos, Certificacoes, UsuarioBase


def create_groups(apps, schema_editor):
    """Cria os grupos de segurança do sistema."""
    
    # ========== GRUPO PRODUTOR ==========
    produtor_group, created = Group.objects.get_or_create(name='Produtor')
    
    if created:
        # Permissões para Produtor
        produtor_permissions = [
            'add_produtos',
            'change_produtos',
            'delete_produtos',
            'view_produtos',
            'add_certificacoes',
            'view_certificacoes',
        ]
        
        for perm in produtor_permissions:
            try:
                permission = Permission.objects.get(codename=perm)
                produtor_group.permissions.add(permission)
            except Permission.DoesNotExist:
                pass
    
    # ========== GRUPO EMPRESA ==========
    empresa_group, created = Group.objects.get_or_create(name='Empresa')
    
    if created:
        # Permissões para Empresa
        empresa_permissions = [
            'view_produtos',
            'add_certificacoes',
            'view_certificacoes',
        ]
        
        for perm in empresa_permissions:
            try:
                permission = Permission.objects.get(codename=perm)
                empresa_group.permissions.add(permission)
            except Permission.DoesNotExist:
                pass
    
    # ========== GRUPO AUDITOR (Admin) ==========
    auditor_group, created = Group.objects.get_or_create(name='Auditor')
    
    if created:
        # Permissões para Auditor (acesso completo)
        auditor_permissions = [
            'view_produtos',
            'view_certificacoes',
            'change_certificacoes',
            'delete_certificacoes',
            'view_usuariobase',
            'view_produtor',
            'view_empresa',
        ]
        
        for perm in auditor_permissions:
            try:
                permission = Permission.objects.get(codename=perm)
                auditor_group.permissions.add(permission)
            except Permission.DoesNotExist:
                pass


def remove_groups(apps, schema_editor):
    """Remove os grupos (para reverter a migration)."""
    Group.objects.filter(name__in=['Produtor', 'Empresa', 'Auditor']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma_certificacao', '0003_usuarioslegado_alter_certificacoes_options_and_more'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
