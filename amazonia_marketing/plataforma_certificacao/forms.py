from django import forms
from .models import Produtos

class ProdutoForm(forms.ModelForm):
    
    # Faz a conexão com o modelo do banco de dados
    molde = Produtos
    
    # Escolhe os campos que irão aparecer para o usuário no HTML    
    fields = ['nome', 'categoria', 'descricao', 'preco', 'imagem']
    
    # Estillização dos campos do formulário (global)
    widgets = {
        'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. Mel'}),
        'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    }