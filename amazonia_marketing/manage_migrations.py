#!/usr/bin/env python
"""
Script para gerenciar e limpar migrations redundantes do Django.

AVISOS IMPORTANTES:
1. Execute este script apenas depois de fazer backup do banco de dados
2. Backup: mysqldump -u django_user -p amazonia_marketing > backup.sql
3. Este script reorganiza o histórico de migrations para evitar conflitos

PASSOS PARA EXECUTAR:
1. python manage.py makemigrations --no-changes (verificar se há alterações)
2. python manage.py migrate --fake-initial (se for primeira vez)
3. python manage.py migrate (aplicar todas as migrations)
4. python manage.py showmigrations (verificar status)
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amazonia_marketing.settings')
django.setup()

from django.core.management import call_command

def main():
    print("=" * 70)
    print("GERENCIADOR DE MIGRATIONS")
    print("=" * 70)
    print()
    print("Este script verifica e exibe o estado das migrations.")
    print()
    
    # Mostrar status das migrations
    print("📋 Status das Migrations Atuais:")
    print("-" * 70)
    call_command('showmigrations', 'plataforma_certificacao', verbosity=2)
    
    print()
    print("✅ Para limpar migrations desatualizadas:")
    print("   1. Faça backup: mysqldump -u django_user -p amazonia_marketing > backup.sql")
    print("   2. Execute: python manage.py makemigrations --no-changes")
    print("   3. Execute: python manage.py migrate")
    print()
    print("⚠️  NOTA: Migrations redundantes são seguras se não alterarem o estado do banco.")
    print("=" * 70)

if __name__ == '__main__':
    main()
