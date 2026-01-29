from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Produtos, Produtor, EmpresaProdutor, Certificacoes, Empresa, CustomUser
)
from django.contrib.auth.models import User
import re

# ============================================================================
# FORMS DE AUTENTICAÇÃO E CADASTRO
# ============================================================================

class CadastroProdutorForm(forms.Form):
    """Formulário para cadastro de novo produtor"""
    email = forms.EmailField(
        max_length=100,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'seu@email.com',
            'required': True
        })
    )
    nome = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nome Completo',
            'required': True
        })
    )
    cpf = forms.CharField(
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '000.000.000-00',
            'id': 'id_cpf'
        })
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '(00) 9999-9999'
        })
    )
    endereco = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Endereço completo'
        })
    )
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Senha forte',
            'required': True
        })
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirme a senha',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('E-mail já está em uso, tente outro.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').strip()
        if cpf:
            cpf_numeros = cpf.replace('.', '').replace('-', '')
            if len(cpf_numeros) != 11:
                raise ValidationError('CPF deve conter 11 dígitos.')
            # Validar se CPF já existe
            if Produtor.objects.filter(cpf=cpf_numeros).exists():
                raise ValidationError('CPF já está em uso, tente outro.')
        return cpf

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError('As senhas não correspondem.')
        
        return cleaned_data

    def save(self):
        """Cria CustomUser com tipo='produtor' e Produtor profile"""
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['senha'],
            nome=self.cleaned_data['nome'],
            tipo='produtor',
            telefone=self.cleaned_data.get('telefone', ''),
            endereco=self.cleaned_data.get('endereco', '')
        )
        
        cpf = self.cleaned_data.get('cpf', '').strip()
        Produtor.objects.create(
            usuario=user,
            cpf=cpf if cpf else None
        )
        
        return user


class CadastroEmpresaForm(forms.Form):
    """Formulário para cadastro de nova empresa"""
    email = forms.EmailField(
        max_length=100,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'seu@empresa.com',
            'required': True
        })
    )
    nome = forms.CharField(
        max_length=100,
        label='Nome de Contato',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nome da Pessoa de Contato',
            'required': True
        })
    )
    cnpj = forms.CharField(
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '00.000.000/0000-00',
            'id': 'id_cnpj'
        })
    )
    razao_social = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Razão Social da Empresa'
        })
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '(00) 9999-9999'
        })
    )
    endereco = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Endereço comercial'
        })
    )
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Senha forte',
            'required': True
        })
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirme a senha',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('E-mail já está em uso, tente outro.')
        return email

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj', '').strip()
        if cnpj:
            # Validar comprimento
            cnpj_numeros = cnpj.replace('.', '').replace('/', '').replace('-', '')
            if len(cnpj_numeros) != 14:
                raise ValidationError('CNPJ deve conter 14 dígitos.')
            
            # Validar se CNPJ já existe
            if EmpresaProdutor.objects.filter(cnpj=cnpj_numeros).exists():
                raise ValidationError('CNPJ já está em uso, tente outro.')
        
        return cnpj

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError('As senhas não correspondem.')
        
        return cleaned_data

    def save(self):
        """Cria CustomUser com tipo='empresa' e EmpresaProdutor profile"""
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['senha'],
            nome=self.cleaned_data['nome'],
            tipo='empresa',
            telefone=self.cleaned_data.get('telefone', ''),
            endereco=self.cleaned_data.get('endereco', '')
        )
        
        cnpj = self.cleaned_data.get('cnpj', '').strip()
        EmpresaProdutor.objects.create(
            usuario=user,
            cnpj=cnpj if cnpj else None,
            razao_social=self.cleaned_data.get('razao_social', '')
        )
        
        return user


# ============================================================================
# FORMS DE EDIÇÃO DE PERFIL
# ============================================================================

class UsuarioBaseConfigForm(forms.ModelForm):
    """Formulário para edição de dados básicos do usuário (CustomUser)"""
    class Meta:
        model = CustomUser
        fields = ['nome', 'email', 'telefone', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome Completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'seu@email.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 99999-9999'}),
            'endereco': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Endereço'}),
        }


class ProdutorConfigForm(forms.ModelForm):
    """Formulário para edição de perfil do produtor"""
    class Meta:
        model = Produtor
        fields = ['cpf', 'bio', 'foto_perfil', 'cidade', 'estado', 'cep', 'whatsapp', 'instagram', 'facebook']
        widgets = {
            'cpf': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '000.000.000-00'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Conte sua história...'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SP'}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-000'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 99999-9999'}),
            'instagram': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '@seu_usuario'}),
            'facebook': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'URL do perfil'}),
        }


class EmpresaConfigForm(forms.ModelForm):
    """Formulário para edição de perfil da empresa"""
    class Meta:
        model = EmpresaProdutor
        fields = ['cnpj', 'razao_social', 'nome_fantasia', 'inscricao_estadual', 
                  'documento_contrato_social', 'documento_cnpj', 'documento_alvara',
                  'endereco_comercial', 'cidade', 'estado', 'cep', 'telefone_comercial', 'site']
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00.000.000/0000-00'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Razão Social'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome Fantasia'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'IE'}),
            'documento_contrato_social': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'}),
            'documento_cnpj': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'}),
            'documento_alvara': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx'}),
            'endereco_comercial': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Endereço'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SP'}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-000'}),
            'telefone_comercial': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 9999-9999'}),
            'site': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://www.empresa.com'}),
        }


# ============================================================================
# FORMS DE CADASTRO DE PRODUTOS E CERTIFICAÇÕES
# ============================================================================

class ProdutoForm(forms.ModelForm):
    """Formulário para cadastro/edição de produtos"""
    class Meta:
        model = Produtos
        fields = ['nome', 'descricao', 'preco', 'imagem', 'status_estoque']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome do produto'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Descrição completa'}),
            'preco': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'imagem': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'status_estoque': forms.Select(attrs={'class': 'form-input'}, choices=[
                ('disponivel', 'Disponível'),
                ('indisponivel', 'Indisponível'),
                ('descontinuado', 'Descontinuado'),
            ]),
        }


# --- FORMULÁRIO 1: EDITAR PERFIL PRODUTOR ---
class EditarPerfilProdutorForm(forms.ModelForm):
    """Formulário para edição de perfil do produtor"""
    class Meta:
        model = Produtor
        fields = ['bio', 'foto_perfil', 'cidade', 'estado', 'cep', 'whatsapp', 'instagram', 'facebook']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Conte sua história...'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Estado'}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-000'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 99999-9999'}),
            'instagram': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '@seu_usuario'}),
            'facebook': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'URL do perfil'}),
        }


class EditarPerfilEmpresaForm(forms.ModelForm):
    """Formulário para edição de perfil da empresa com validação obrigatória de documentos"""
    
    class Meta:
        model = EmpresaProdutor
        fields = ['cnpj', 'razao_social', 'nome_fantasia', 'inscricao_estadual',
                  'documento_contrato_social', 'documento_cnpj', 'documento_alvara',
                  'endereco_comercial', 'cidade', 'estado', 'cep', 'telefone_comercial', 'site', 'logo', 'descricao_empresa']
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00.000.000/0000-00'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Razão Social', 'required': True}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome Fantasia'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'IE'}),
            'documento_contrato_social': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx', 'required': True}),
            'documento_cnpj': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx', 'required': True}),
            'documento_alvara': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx', 'required': True}),
            'endereco_comercial': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Endereço', 'required': True}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cidade', 'required': True}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'SP', 'required': True}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-000', 'required': True}),
            'telefone_comercial': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 9999-9999', 'required': True}),
            'site': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://www.empresa.com'}),
            'logo': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'descricao_empresa': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Descreva sua empresa...'}),
        }
    
    def clean(self):
        """Validação customizada para documentos obrigatórios"""
        cleaned_data = super().clean()
        
        # Validar documentos obrigatórios
        documento_cnpj = cleaned_data.get('documento_cnpj')
        documento_contrato = cleaned_data.get('documento_contrato_social')
        documento_alvara = cleaned_data.get('documento_alvara')
        
        if not documento_cnpj and not self.instance.documento_cnpj:
            self.add_error('documento_cnpj', 'Documento CNPJ é obrigatório para verificação.')
        
        if not documento_contrato and not self.instance.documento_contrato_social:
            self.add_error('documento_contrato_social', 'Contrato Social/Estatuto é obrigatório para verificação.')
        
        if not documento_alvara and not self.instance.documento_alvara:
            self.add_error('documento_alvara', 'Alvará de Funcionamento é obrigatório para verificação.')
        
        # Validar tamanho dos arquivos (máximo 5MB)
        for campo in ['documento_cnpj', 'documento_contrato_social', 'documento_alvara']:
            arquivo = cleaned_data.get(campo)
            if arquivo and arquivo.size > 5 * 1024 * 1024:  # 5MB
                self.add_error(campo, f'Arquivo muito grande. Máximo 5MB permitido.')
        
        return cleaned_data


class CertificacaoForm(forms.ModelForm):
    """Formulário para submissão de certificação de produto"""
    class Meta:
        model = Certificacoes
        fields = ['texto_autodeclaracao', 'documento', 'documento_2', 'documento_3']
        widgets = {
            'texto_autodeclaracao': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 6,
                'placeholder': 'Declare os critérios que seu produto atende...'
            }),
            'documento': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.jpg,.png'
            }),
            'documento_2': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.jpg,.png'
            }),
            'documento_3': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.jpg,.png'
            }),
        }
        labels = {
            'texto_autodeclaracao': 'Autodeclaração',
            'documento': 'Documento de Suporte (PDF ou Imagem) - Principal',
            'documento_2': 'Documento Adicional 2 (Opcional)',
            'documento_3': 'Documento Adicional 3 (Opcional)',
        }


class CertificacaoMultiplaForm(forms.Form):
    """Formulário para submissão de certificação em múltiplos produtos"""
    texto_autodeclaracao = forms.CharField(
        label='Autodeclaração',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 6,
            'placeholder': 'Declare os critérios que seus produtos atendem...'
        })
    )
    arquivo_autodeclaracao = forms.FileField(
        label='Documento de Suporte (PDF ou Imagem)',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        })
    )
    produtos = forms.ModelMultipleChoiceField(
        label='Selecione os Produtos',
        queryset=Produtos.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'})
    )

    def __init__(self, usuario=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario:
            self.fields['produtos'].queryset = Produtos.objects.filter(usuario=usuario, status_estoque='disponivel')
