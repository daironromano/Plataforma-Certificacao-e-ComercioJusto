# ------
from django.shortcuts import render, redirect, get_object_or_404
# Importanto ferramentas de segurança nativa do django
from django.contrib.auth import authenticate, login, logout
# Verifica a autenticação do login
from django.contrib.auth.decorators import login_required
# Importar modulo de alerta sucesso ou erro
from django.contrib import messages
# Importar novos modelos do banco 
from .models import CustomUser, Produtos,Certificacoes
# Importamos a classe ProdutoForm que criamos no forms.py
from .forms import ProdutoForm, ProdutoComAutodeclaracaoForm
# Importamos datetime
from datetime import datetime
# Para conseguir calcular os dados
from django.db.models import Count




# --- Função para exibir tela inicial ---
def home_publica(request):
    # Filtra apenas produtos disponíveis e armazena na variável
    produtos = Produtos.objects.filter(status_estoque='disponivel')
    
    # Filtrando apenas os produtos com selo aprovado
    ids_com_selo = Certificacoes.objects.filter(status_certificacao='aprovado').values_list('produto_id', flat=True)
    # Marcando os produtos antes de enviar para o front (com/sem selo)
    for p in produtos:
        if p.id_produto in ids_com_selo:
            p.tem_selo = True
        else:
            p.tem_selo = False
        
    return render(request, 'index.html', {'produtos': produtos})

# Lógica para redicionar o usuário de acordo com o seu tipo 
def redirecionar_por_tipo(user):
    if user.tipo_usuario == 'produtor':
        return redirect('home_produtor')
    elif user.tipo_usuario == 'empresa':
        return redirect('home_empresa') # Falta criar
    elif user.tipo_usuario == 'auditor':
        return redirect('home_admin')
    elif user.is_superuser:
        return redirect('/admin/')
    else:
        return redirect('home_padrao')

# --- Função para fazer login no sistema (Atualizada com ferramentas nativas do django) ---
def login_usuarios(request):
    if request.user.is_authenticated:
        return redirecionar_por_tipo(request.user)
    
    # Pegamos os dados do html 
    if request.method == 'POST':
        email_form = request.POST.get('email')
        senha_form = request.POST.get('senha')
        # authenticate: Verifica se user e senha batem de forma segura.
        user = authenticate(request, username=email_form, password=senha_form)
        
        # Cria a sessão no navegador (o cookie seguro)
        if user is not None:
            login(request, user)
            # Essa função decide para onde o usuário vai pelo seu tipo
            return redirecionar_por_tipo(user)
        else: 
            messages.error(request, 'Usuário ou senha inválidos.')
            
    return render(request, 'registration/login.html')

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

# -- DASHBOARD DO ADMINISTRADOR ---
@verificar_autenticacao
def home_admin(request):
    # Segurança extra: Garante que só ADMIN entra aqui
    if request.session.get('usuario_tipo') != 'admin':
        messages.error(request, 'Acesso restrito a administradores!')
        return redirect('login')
    
    # Métricas para exibir no dashboard 
    # Contamos quantos pedidos existem em cada fila 
    pendente = Certificacoes.objects.filter(status_certificacao='pendente').count()
    aprovado = Certificacoes.objects.filter(status_certificacao='aprovado').count()
    reprovado = Certificacoes.objects.filter(status_certificacao='reprovado').count()
    
    # Prepara os dados para serem enviados para o HTML
    contexto = {
        'pendente': pendente,
        'aprovado': aprovado,
        'reprovado': reprovado,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    return render(request, 'home_admin.html', contexto)

# Função para visualização dos certificados pelo administrador
@verificar_autenticacao
def admin_visualizar_certificados(request):
    # Segurança para garantir que apenas usuário do tipo admin visualizem os certificados
    if request.session.get('usuario_tipo') != 'admin':
        return redirect('login')
    # Filtro para saber as auditorias pendentes 
    status_filtro = request.GET.get('status')
    # Consultando produtos e usuários juntos com 'select_related'
    consulta = Certificacoes.objects.select_related('produto', 'produto__usuario').all().order_by('-data_envio')
    if status_filtro: 
        consulta = consulta.filter(status_certificacao=status_filtro)

    contexto = {
        'certificacoes': consulta,
        'status_filtro': status_filtro,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    
    return render(request, 'admin_certificacoes.html', contexto)

# Função que o botão aprovar irá chamar
@verificar_autenticacao
def admin_responder_certificacoes(request, certificacao_id):
    # Segurança: garantindo que somente admin possa ter essa ação
    if request.session.get('usuario_tipo') != 'admin':
        return redirect('login')
    
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao') # Pega o valor dobotão 
        admin_id = request.session.get('usuario_id')
        
        if acao == 'aprovar':
            certificacao.status_certificacao = 'aprovado'
            messages.success(request, f'Certificação APROVADA para o produto {certificacao.produto.nome}!')
        elif acao == 'rejeitar':
            certificacao.status_certificacao = 'reprovado'
            messages.warning(request, f'Certificação REJEITADA para o produto {certificacao.produto.nome}.')
        
        # Auditoria: Registra quem fez e quando
        certificacao.data_resposta = datetime.now().date()
        certificacao.admin_responsavel_id = admin_id
        certificacao.save() # Atualiza no Banco
        
        return redirect('admin_visualizar_certificacoes')
    
    return redirect('home_admin')

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

