from django.shortcuts import render, redirect

# Importamos a classe Usuarios que acabou de ser criada no models.py
from .models import Usuarios

# Função para fazer login no sistema
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
           
#Função para fazer login no sistema
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

    return render(request, 'login.html', {'msg': msg})

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

# Função para deslogar o usuário
def logout_view(request):
    # Limpa a sessão (desloga)
    request.session.flush()
    return redirect('login')

# Função para cadastrar novo usuário

# Função para adicionar certificação ao produto

# Função para adicionar produtos

# Função para empresa comprar produtos de produtor

