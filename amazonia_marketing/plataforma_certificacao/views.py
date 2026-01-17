from django.shortcuts import render, redirect
# Importamos as classes que criamos no models.py
from .models import Usuarios, Produtos, Certificacoes
# Importamos a classe ProdutoForm que criamos no forms.py
from .forms import ProdutoForm, ProdutoComAutodeclaracaoForm
# Importamos datetime
from datetime import datetime
# Importar modulo de alerta sucesso ou erro
from django.contrib import messages
# Para conseguir calcular os dados
from django.db.models import Count
# ------
from django.shortcuts import get_object_or_404



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
    
    return render(request, 'registration/login.html', {'msg': msg })

# --- Função de Segurança (Decorador) ---
# Se alguém tentar acessar direto pela URL sem logar, essa função chuta de volta.
def verificar_autenticacao(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login') # Chuta para o login
        return view_func(request, *args, **kwargs)
    return wrapper

# --- As Telas Protegidas ---

# --- DASHBOARD DO PRODUTOR ---
@verificar_autenticacao
def home_produtor(request):
    # Segurança extra: Garante que só PRODUTOR entra aqui
    if request.session.get('usuario_tipo') != 'produtor':
         return redirect('login')
    
    # Identifica quem é o produtor logado
    usuario_id = request.session.get('usuario_id')
    # Filtra produtos que o dono é o usuário logado
    produtos = Produtos.objects.filter(usuario_id=usuario_id)
    
    # CÁLCULO DE ALGUMAS MÉTRICAS PARA EXIBIR NO PERFIL DO PRODUTOR (FEEDBACK)
    # -- Quantos produtos ele cadastrados -- 
    total_produtos = produtos.count()
    
    # -- Quantas certificações ele tem pendente --
    pendentes = Certificacoes.objects.filter(
        produto__usuario_id = usuario_id,
        status_certificacao = 'pendente',
    ).count()
    
    # -- Quantas certificacoes ele tem aprovadas --
    aprovados = Certificacoes.objects.filter(
        produto__usuario_id = usuario_id,
        status_certificacao = 'aprovado',
    ).count()
    
    # Lógica para entregar produtos cadastros para o frontend (HTML)
    contexto = {
        'produtos': produtos,
        'total_produtos': total_produtos,
        'pendentes': pendentes,
        'aprovados': aprovados,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    
    # Renderiza a tela passando o nome do usuário para o HTML
    return render(request, 'home_produtor.html', contexto)

# --- ENVIO DE DOCUMENTO PELO PRODUTOR (AUTODECLARAÇÃO) ---
@verificar_autenticacao
def enviar_autodeclaracao(request):
    # Segurança de perfil, garante que só o produtor faça o envio
    if request.session.get('usuario_tipo') != 'produtor':
        return redirect('home_padrao')
    # Identificando o usuário logado
    usuario_id = request.session.get('usuario_id')
    # Processando o formulário (POST)
    if request.method == 'POST':
        form = ProdutoComAutodeclaracaoForm(request.POST, request.FILES)
        form.fields['produto'].queryset = Produtos.objects.filter(usuario_id=usuario_id)
        
        if form.is_valid():
            # Extrair os dados do formulário
            produto_selecionado = form.cleaned_data['produto']
            texto = form.cleaned_data['texto_autodeclaracao']
            arquivo = form.cleaned_data['arquivo_autodeclaracao']
            
            # 5. Regra de Negócio: Criação da Certificação
            nova_certificacao = Certificacoes(
                # Extraindo os dados do formulário
                produto = produto_selecionado,
                texto_autodeclaracao = texto,
                # Se tiver arquivo, salva o arquivo. Se não, salva None.
                documento = arquivo,
                # Implementado a lógica de negócio: status nasce como pendente até um admin aprovar
                status_certificacao = 'pendente',
                data_envio = datetime.now().date(),
                
                # Admin responsável começa vazio (ninguém aprovou ainda)
                admin_responsavel = None,
            )
            
            nova_certificacao.save()
            # Feedback e redicionamento 
            messages.success(request, 'Documento enviado com sucesso! Aguardo a análise do auditor')            
            return redirect('home_produtor')
    else:
        # Considera que é um GET: exibe a tela inicial
        form = ProdutoComAutodeclaracaoForm()
        # Aqui mostramos apenas os produtos que o usuario logado é dono
        form.fields['produto'].queryset = Produtos.objects.filter(usuario_id=usuario_id)
        
    contexto = {
        'form': form,
        'usuario_nome': request.session.get('usuario_nome')
    }
    
    return render(request, 'enviar_autodeclaracao.html', contexto)

# ---  Função para o produtor adicionar produtos ---
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
            produto.status_estoque = 'disponivel'
            
            # Agora salvaremos no banco de dados as alterações e retornamos a home_produtor
            produto.save()
            
            # Feedback para o usuário (UX)
            messages.success(request, f'O produto {produto.nome} foi cadastrado')
            
            return redirect('home_produtor')
        
    else:
            # se for um GET apenas mostra o formulário para o usário
        form = ProdutoForm()
        
        # Agora sim o formulário é enviado (renderizado) para o HTML
    return render(request, 'cadastro_produto.html', {'form': form}) 
        
@verificar_autenticacao
# Função deleta em cascata 
def deletar_produto(request, produto_id):
    # Garantir que o produto existe para poder fazer algo com ele
    produto = get_object_or_404(Produtos, id_produto=produto_id)
    # Segurança para garantir que o usuário logado é o dono do produto cadastrado
    id_logado = request.session.get('usuario_id')
    if produto.usuario_id != id_logado:
        messages.error(request, 'Tentativa de exclusão falha. Você não é o dono do produto!')
        return redirect('home_prdutor')
    # Antes de apagar, verifica se tem certificado e deleta também para não ter erro de integridade
    certificacoes_vinculadas = Certificacoes.objects.filter(produto_id=produto_id)
    if certificacoes_vinculadas.exists():
        qtde = certificacoes_vinculadas.count()
        certificacoes_vinculadas.delete()
        print(f'Sistema: {qtde} certificações deletadas em cascata para o produto {produto_id}')
    
    # Excluindo o produto (se você for o dono dele)
    nome_produto = produto.nome 
    produto.delete()
    # Feedback para o usuário
    messages.success(request, f'Produto: {nome_produto} removido!')   
    return redirect('home_produtor')
    
    





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

# ---  Função para empresa comprar produtos de produtor ---

