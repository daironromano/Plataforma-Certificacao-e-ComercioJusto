from django import forms
from .models import Certificacoes, Produtos
from django.core.exceptions import ValidationError
from django.conf import settings


class CertificacaoForm(forms.ModelForm):
    """Formulário para cadastro de certificação com upload de autodeclaração"""
    
    class Meta:
        model = Certificacoes
        fields = ['texto_autodeclaracao', 'arquivo_autodeclaracao']
        widgets = {
            'texto_autodeclaracao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Digite aqui o texto da sua autodeclaração (opcional)',
                'style': 'font-size: 14px;'
            }),
            'arquivo_autodeclaracao': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'id': 'arquivo_input'
            }),
        }
        labels = {
            'texto_autodeclaracao': 'Texto da Autodeclaração',
            'arquivo_autodeclaracao': 'Arquivo de Autodeclaração (PDF, DOC, DOCX, JPG, PNG)',
        }
        help_texts = {
            'arquivo_autodeclaracao': 'Máximo de 5MB. Formatos aceitos: PDF, DOC, DOCX, JPG, PNG',
        }

    def clean_arquivo_autodeclaracao(self):
        """Validação customizada do arquivo"""
        arquivo = self.cleaned_data.get('arquivo_autodeclaracao')
        
        if arquivo:
            # Validar tamanho
            if arquivo.size > 5242880:  # 5MB
                raise ValidationError('O arquivo não pode exceder 5MB.')
            
            # Validar extensão
            extensoes_permitidas = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            extensao_arquivo = arquivo.name.split('.')[-1].lower()
            
            if extensao_arquivo not in extensoes_permitidas:
                raise ValidationError(
                    f'Tipo de arquivo não permitido. Aceitos: {", ".join(extensoes_permitidas)}'
                )
            
            # Validar tipo MIME
            tipos_mime_permitidos = settings.ALLOWED_UPLOAD_MIME_TYPES
            if arquivo.content_type not in tipos_mime_permitidos:
                raise ValidationError('Tipo MIME do arquivo não é permitido.')
        
        return arquivo

    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto_autodeclaracao')
        arquivo = cleaned_data.get('arquivo_autodeclaracao')
        
        # Exigir pelo menos um: texto OU arquivo
        if not texto and not arquivo:
            raise ValidationError(
                'É necessário preenchero texto da autodeclaração ou enviar um arquivo.'
            )
        
        return cleaned_data


class ProdutoComAutodeclaracaoForm(forms.Form):
    """Formulário para selecionar um produto e enviar autodeclaração"""
    
    produto = forms.ModelChoiceField(
        queryset=Produtos.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'produto_select'
        }),
        label='Selecione o Produto',
        empty_label='-- Escolha um produto --'
    )
    
    texto_autodeclaracao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Digite aqui o texto da sua autodeclaração (opcional)',
            'style': 'font-size: 14px;'
        }),
        label='Texto da Autodeclaração'
    )
    
    arquivo_autodeclaracao = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
            'id': 'arquivo_input'
        }),
        label='Arquivo de Autodeclaração',
        help_text='PDF, DOC, DOCX, JPG, PNG. Máximo 5MB.'
    )
    
    def clean_arquivo_autodeclaracao(self):
        """Validação customizada do arquivo"""
        arquivo = self.cleaned_data.get('arquivo_autodeclaracao')
        
        if arquivo:
            # Validar tamanho
            if arquivo.size > 5242880:  # 5MB
                raise ValidationError('O arquivo não pode exceder 5MB.')
            
            # Validar extensão
            extensoes_permitidas = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            extensao_arquivo = arquivo.name.split('.')[-1].lower()
            
            if extensao_arquivo not in extensoes_permitidas:
                raise ValidationError(
                    f'Tipo de arquivo não permitido. Aceitos: {", ".join(extensoes_permitidas)}'
                )
            
            # Validar tipo MIME
            tipos_mime_permitidos = settings.ALLOWED_UPLOAD_MIME_TYPES
            if arquivo.content_type not in tipos_mime_permitidos:
                raise ValidationError('Tipo MIME do arquivo não é permitido.')
        
        return arquivo

    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto_autodeclaracao')
        arquivo = cleaned_data.get('arquivo_autodeclaracao')
        
        # Exigir pelo menos um: texto OU arquivo
        if not texto and not arquivo:
            raise ValidationError(
                'É necessário preencher o texto da autodeclaração ou enviar um arquivo.'
            )
        
        return cleaned_data
