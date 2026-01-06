from django.shortcuts import render, redirect
# Importamos a classe Usuarios que acabou de ser criada no models.py
from .models import Usuarios 

def login_view(request):
    msg = None
    if request.method == 'POST':
        # Pega os dados do formulário HTML
        email_form = request.POST.get('email')
        senha_form = request.POST.get('senha')
        
        try:
            # BUSCA NO BANCO:
            # Procura um usuario onde o email E a senha batem com o formulário
            usuario = Usuarios.objects.get(email=email_form, senha=senha_form)
            
            # SUCESSO! Salva os dados na "Sessão" (memória do navegador)
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_tipo'] = usuario.tipo
            request.session['usuario_nome'] = usuario.nome
            
            # LÓGICA DE REDIRECIONAMENTO (O requisito da Sprint 3)
            # Verifica o campo 'tipo' que veio do banco de dados
            if usuario.tipo == 'produtor':
                return redirect('home_produtor')
            elif usuario.tipo == 'admin':
                return redirect('home_admin')
            else:
                return redirect('home_padrao')

        except Usuarios.DoesNotExist:
            # Se não achar ninguém com esse email/senha
            msg = "Usuário ou senha inválidos. Tente novamente."

    return render(request, 'login.html', {'msg': msg})

# --- Função de Segurança (Bloqueio) ---
# Se alguém tentar acessar direto pela URL sem logar, essa função chuta de volta
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
def home_admin(request):
    # Segurança extra: Garante que só ADMIN entra aqui
    if request.session.get('usuario_tipo') != 'admin':
         return redirect('login')
    return render(request, 'home_admin.html')

@verificar_autenticacao
def home_padrao(request):
    return render(request, 'home.html')

def logout_view(request):
    # Limpa a sessão (desloga)
    request.session.flush()
    return redirect('login')