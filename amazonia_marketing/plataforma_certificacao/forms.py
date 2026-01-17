from django import forms
from .models import Produtos

class ProdutoForm(forms.ModelForm):
    # Faz a conexão com o modelo do banco de dados e diz qual modelo usar
    class Meta:
        model = Produtos
        # Escolhe os campos que irão aparecer para o usuário no HTML    
        fields = ['nome', 'categoria', 'descricao', 'preco', 'imagem']
    
        # Estillização dos campos do formulário (global)
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Mel de Jataí'}),
            'categoria': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }