from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import CustomUser, PerfilProduto, PerfilEmpresa, Produtos, Certificacoes
from django.contrib.auth.forms import UserCreationForm

# --- Princípio DRY - Don't Repeat Yourself ---
def validar_arquivo_seguro(arquivo):
    """
    Função isolada para validar arquivos. 
    Pode ser reutilizada em qualquer formulário do sistema.
    """
    if not arquivo:
        return arquivo

    # 1. Validação de Tamanho (Regra de Negócio: Máx 5MB)
    limite_mb = 5
    if arquivo.size > limite_mb * 1024 * 1024: # Convertendo MB para Bytes
        raise ValidationError(f'O arquivo não pode exceder {limite_mb} MB.')
    
    # 2. Validação de Extensão (Segurança básica)
    extensoes_permitidas = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
    # Pega o nome "documento.pdf", separa no ponto e pega a última parte "pdf"
    extensao = arquivo.name.split('.')[-1].lower()
    # Verifica a lista de extensões permitidas e retorna erro se não estiver lá
    if extensao not in extensoes_permitidas:
        raise ValidationError(f'Extensão não permitida. Use: {", ".join(extensoes_permitidas)}')

    # 3. Validação de Tipo MIME (Segurança avançada)
    # Verifica se a constante existe no settings para evitar erro se esquecermos de configurar
    if hasattr(settings, 'ALLOWED_UPLOAD_MIME_TYPES'):
        # arquivo.content_type é o tipo real do arquivo (ex: 'application/pdf')
        if arquivo.content_type not in settings.ALLOWED_UPLOAD_MIME_TYPES:
            raise ValidationError('Tipo de arquivo inválido (MIME type rejeitado).')
    
    return arquivo


# --- FORMULÁRIO 1: CADASTRO DE PRODUTO ---
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produtos
        fields = ['nome', 'categoria', 'descricao', 'preco', 'imagem']
        # Design System: Mantemos a classe 'form-input' para consistência visual (garantindo a identidade do cliente)
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Mel de Jataí'}),
            'categoria': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }
    
    # Aplicamos a validação de segurança também na foto do produto!
    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')
        return validar_arquivo_seguro(imagem)


# --- FORMULÁRIO 2: CERTIFICAÇÃO (Entrega da Sprint 4) ---
class ProdutoComAutodeclaracaoForm(forms.Form): # Formulário híbrido, por isso não herda ModelForm
    # Campo 1: Select (Menu) para escolher qual produto certificar
    produto = forms.ModelChoiceField(
        queryset=Produtos.objects.none(), # Segurança: Começa vazio, a View vai preencher
        label='Selecione o Produto',
        empty_label='-- Escolha um produto --',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    # Campo 2: Texto livre
    texto_autodeclaracao = forms.CharField(
        required=False, # Opcional (pode mandar só arquivo)
        label='Texto da Autodeclaração',
        widget=forms.Textarea(attrs={
            'class': 'form-input', 
            'rows': 5,
            'placeholder': 'Escreva aqui sua declaração se não tiver o arquivo PDF...'
        })
    )
    
    # Campo 3: Upload do arquivo
    arquivo_autodeclaracao = forms.FileField(
        required=False, # Opcional (pode mandar só texto)
        label='Arquivo (PDF/Foto)',
        help_text='Máximo 5MB.',
        widget=forms.FileInput(attrs={'class': 'form-input'})
    )

    # Validação Específica: Chama nossa função validar_arquivo_seguro (garante o DRY)
    def clean_arquivo_autodeclaracao(self):
        arquivo = self.cleaned_data.get('arquivo_autodeclaracao')
        return validar_arquivo_seguro(arquivo)

    # Validação Geral: (Cross-field validation - Validação cruzada)
    def clean(self):
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto_autodeclaracao')
        arquivo = cleaned_data.get('arquivo_autodeclaracao')
        
        # Regra de Negócio: Não pode enviar tudo vazio
        if not texto and not arquivo:
            raise ValidationError('Por favor, preencha o texto OU envie um arquivo.')

        return cleaned_data
    
    
# FORMULÁRIO DE CADASTRO DO USUÁRIO
class CadastroUsuarioForm(UserCreationForm):
    # Campos extras que não existem no formulário padrão
    nome_completo = forms.CharField(max_length=50, help_text='Nome da Fazenda ou Razão Social')
    email = forms.EmailField(required=True)
    
    # O seletor de topo 
    TIPO_CHOICES = (
        ('produtor', 'Sou Produtor'),
        ('empresa', 'Sou Empresa')
    )
    tipo_usuario = forms.ChoiceField(choices=TIPO_CHOICES, widget=forms.RadioSelect)
    
    # Campos específicos (inicialmente opcionais na validação visual, mas tratados no backend)
    cpf = forms.CharField(max_length=11, label="CPF", required=False)
    cnpj = forms.CharField(max_length=14, label="CNPJ", required=False)
    endereco = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    class Meta:
        model = CustomUser
        # Definimos quais campos do Model aparecem no HTML e na ordem certa
        fields = ('username', 'email', 'nome_completo', 'tipo_usuario', 'cpf', 'cnpj', 'endereco')
        
    # Validação Inteligente para saber qual foi escolhido
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_usuario')
        cpf = cleaned_data.get('cpf')
        cnpj = cleaned_data.get('cnpj')
        
        # Regra 1: Se for Produtor, TEM que ter CPF
        if tipo == 'produtor':
            if not cpf:
                self.add_error('cpf', 'O CPF é obrigatório para produtores.')
            # Limpa o CNPJ para não salvar lixo
            cleaned_data['cnpj'] = None
            
        # Regra 2: Se for Empresa, TEM que ter CNPJ
        elif tipo == 'empresa':
            if not cnpj:
                self.add_error('cnpj', 'O CNPJ é obrigatório para empresas.')
            # Limpa o CPF para não salvar lixo
            cleaned_data['cpf'] = None

        return cleaned_data
    
    def save(self, commit=True):
        # 1. Salva o Usuário Pai (CustomUser) primeiro
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nome_completo'] # Usamos first_name para guardar o nome exibido
        user.tipo_usuario = self.cleaned_data['tipo_usuario']
        
        if commit:
            user.save()
            # Salva no perfil correto baseado na escolha
            cpf_limpo = self.cleaned_data['cpf']
            if user.tipo_usuario == 'produtor':
                PerfilProduto.objects.create(
                    user=user,
                    nome=self.cleaned_data['nome_completo'],
                    cpf=cpf_limpo,
                    endereco=self.cleaned_data['endereco']
                )
            elif user.tipo_usuario == 'empresa':
                cnpj_limpo = self.cleaned_data['cnpj']

                PerfilEmpresa.objects.create(
                    user=user,
                    razao_social=self.cleaned_data['nome_completo'],
                    cnpj=cnpj_limpo
                )
        return user