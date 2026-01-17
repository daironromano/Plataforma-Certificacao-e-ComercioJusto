from django.shortcuts import render, redirect

# Importamos a classe Usuarios que acabou de ser criada no models.py
from .models import Usuarios, Produtos
# Importamos a classe ProdutoForm que criamos no forms.py
from .forms import ProdutoForm


# --- Função para exibir tela inicial ---
def home_publica(request):
    # Filtra apenas produtos disponíveis e armazena na variável
    produtos_disponiveis = Produtos.objects.filter(status_estoque='diponivel')
    # Dados que o frontend precisa receber 
    dados_front = {
        'produtos': produtos_disponiveis,
        'usuario_logado': request.session.get('usuario_nome'),
    }

    return render(request, 'index.html', dados_front)

# --- Função para fazer login no sistema ---
def login_usuarios(request):
    msg = None
    if request.method == 'POST':
        email_form = request.POST.get('email')
        senha_form = request.POST.get('senha')
        
        # BUSCAR NO BANCO
        try:
            # Procura o usuário que tentou fazer o login no banco de dados
            usuario = Usuarios.objects.get(email=email_form, senha=senha_form)
            
            # Usuário existe: salva os dados da sessão 
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_tipo'] = usuario.tipo
            request.session['usuario_nome'] = usuario.nome
            
            # Lógica para redicionar o usuário de acordo com o seu tipo
            if usuario.tipo == 'produtor':
                return redirect('home_produtor')
            elif usuario.tipo == 'empresa':
                return redirect('home_empresa')
            elif usuario.tipo == 'admin':
                return redirect('home_admin')
            else:
                return redirect('home_padrao')
            
        # Caso não encontre ninguém com o email ou senha inseridos    
        except Usuarios.DoesNotExist:
            msg = 'Usuário ou senha inválidos. Tente novamente'
    
    return render(request, 'login.html', {'msg': msg })
   
# --- Função para fazer login no sistema ---
def login_usuarios(request):
    msg = None
    if request.method == 'POST':
        # Pega os dados do formulário HTML.
        email_form = request.POST.get('email')
        senha_form = request.POST.get('senha')
        
        try:
            # BUSCA NO BANCO:
            # Procura um usuario onde o email e a senha correspondem com o formulário.
            usuario = Usuarios.objects.get(email=email_form, senha=senha_form)
            
            # SUCESSO! Salva os dados na "sessão" (memória do navegador).
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_tipo'] = usuario.tipo
            request.session['usuario_nome'] = usuario.nome
            
            # LÓGICA DE REDIRECIONAMENTO (O requisito da Sprint 3).
            # Verifica o campo 'tipo' que veio do banco de dados
            if usuario.tipo == 'produtor':
                return redirect('home_produtor')
            elif usuario.tipo == 'admin':
                return redirect('home_admin')
            elif usuario.tipo == 'empresa':
                return redirect('home_empresa')
            else:
                return redirect('home_padrao')

        except Usuarios.DoesNotExist:
            # Se não achar ninguém com esse email/senha
            msg = "Usuário ou senha inválidos. Tente novamente."

    return render(request, 'registration/login.html', {'msg': msg})

# --- Função de Segurança (Decorador) ---
# Se alguém tentar acessar direto pela URL sem logar, essa função chuta de volta.
def verificar_autenticacao(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login') # Chuta para o login
        return view_func(request, *args, **kwargs)
    return wrapper

# --- As Telas Protegidas ---
@verificar_autenticacao
def home_produtor(request):
    # Segurança extra: Garante que só PRODUTOR entra aqui
    if request.session.get('usuario_tipo') != 'produtor':
         return redirect('login')
    # Renderiza a tela passando o nome do usuário para o HTML
    return render(request, 'home_produtor.html')

@verificar_autenticacao
def home_empresa(request):
    # Segurança extra: Garante que só EMPRESA entra aqui
    if request.session.get('usuario_tipo') != 'empresa':
         return redirect('login')
        # Renderiza a tela passando o nome do usuário para o HTML
    return render(request, 'home_empresa.html')

@verificar_autenticacao
def home_admin(request):
    # Segurança extra: Garante que só ADMIN entra aqui
    if request.session.get('usuario_tipo') != 'admin':
         return redirect('login')
    return render(request, 'home_admin.html')

@verificar_autenticacao
def home_padrao(request):
    return render(request, 'home.html')

# --- Função para deslogar o usuário ---
def logout_view(request):
    # Limpa a sessão (desloga)
    request.session.flush()
    return redirect('login')
  
# --- Função para cadastrar novo usuário ---

# ---  Função para adicionar certificação ao produto ---

# ---  Função para adicionar produtos ---
@verificar_autenticacao
def cadastro_produto(request):
    # Adiciona nova camada de segurança para garantir que apenas usuários do tipo 'produtor' possam cadastrar produto
    if request.session.get('usuario_tipo') != 'produtor':
        return redirect('home_padrao') 
    
    # Testa qual é a ação que o usuário está fazendo, se é do tipo POST
    if request.method == 'POST':
        # Se sim, a variável 'form' irá receber os dados (POST) e arquivos (FILES)
        form = ProdutoForm(request.POST, request.FILES)
        # Garantindo consistência dos dados
        if form.is_valid():
            produto = form.save(commit=False) # Cria o objeto na memória, mas não salva no banco ainda.
            
            # Definindo o dono manualmente através da sessão
            id_dono = request.session.get('usuario_id')
            produto.usuario = Usuarios.objects.get(id_usuario=id_dono)
            
            # Definindo o status do produto para 'disponível'
            produto.status_estoque = 'disponível'
            
            # Agora salvaremos no banco de dados as alterações e retornamos a home_produtor
            form.save()
            return rendirect('home_produtor')
        
        else:
            # se for um GET apenas mostra o formulário para o usário
            form = ProdutoForm()
        
        # Agora sim o formulário é enviado (renderizado) para o HTML
        return render(request, 'cadastro_produto.html', {'form': form}) 
        
# ---  Função para empresa comprar produtos de produtor ---

