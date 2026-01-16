from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma_certificacao', '0005_alter_certificacoes_table_alter_marketplace_table_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificacoes',
            name='arquivo_autodeclaracao',
            field=models.FileField(blank=True, null=True, upload_to='autodeclaracoes/%Y/%m/%d/'),
        ),
    ]
