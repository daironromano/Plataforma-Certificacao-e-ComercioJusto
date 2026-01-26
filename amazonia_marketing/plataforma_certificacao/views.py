# IMPORTAÇÕES ====================================================================
# render: monta o HTML final
# redirect: manda o usuário para outra URL.
# get_object_or_404: tenta buscar no banco; se não achar, mostra erro 404 (não encontrado) em vez de travar o site.
from django.shortcuts import render, redirect, get_object_or_404
# Ferramentas de segurança nativas do Django 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# Sistema de mensagens (Aquelas faixas verdes/vermelhas de feedback)
from django.contrib import messages
# Nossos modelos (As tabelas do Banco de Dados)
from .models import CustomUser, Produtos, Certificacoes
# Nossos formulários (A validação dos dados que entram)
from .forms import ProdutoForm, ProdutoComAutodeclaracaoForm, CadastroUsuarioForm
# Utilitários (ferramentas úteis para data e contagem)
from datetime import datetime
from django.db.models import Count

# ==============================================================================
# 1. ÁREA PÚBLICA E AUTENTICAÇÃO
# ==============================================================================

def home_publica(request):
    """
    View da página inicial (Vitrine).
    Acessível para qualquer pessoa (logada ou não)
    """
    # Filtra apenas produtos disponíveis no estoque
    produtos = Produtos.objects.filter(status_estoque='disponivel')
    
    # Filtrando apenas os produtos com selo aprovado pelo ID
    ids_com_selo = Certificacoes.objects.filter(status_certificacao='aprovado').values_list('produto_id', flat=True)
    
    # Marcando os produtos que tem selo antes de enviar para o front
    for p in produtos:
        if p.id_produto in ids_com_selo:
            p.tem_selo = True # Criamos esse atributo na memória (não vai pro banco)
        else:
            p.tem_selo = False
            
    # Entregamos a lista processada para o template desenhar.
    return render(request, 'index.html', {'produtos': produtos})

def redirecionar_por_tipo(user):
    """
    Função auxiliar que decide para onde o usuário vai.
    Centraliza a inteligência de 'Para onde cada um vai?'.
    Evita ter que repetir esses IFs no login e no cadastro.
    """
    if user.tipo_usuario == 'produtor':
        return redirect('home_produtor')
    elif user.tipo_usuario == 'empresa':
        return redirect('home_empresa')
    elif user.tipo_usuario == 'auditor':
        return redirect('home_admin')
    elif user.is_superuser:
        return redirect('/admin/')
    else:
        return redirect('home_publica')

def login_usuarios(request):
    """
    View de Login Seguro.
    Substitui a lógica manual antiga por 'authenticate()'.
    """
    
    # Se o cara já está logado, não deixa ele ver a tela de login. Joga pro painel.
    if request.user.is_authenticated:
        return redirecionar_por_tipo(request.user)
    
    # Se ele preencheu o formulário e clicou "Entrar"...
    if request.method == 'POST':
        # Django Auth espera 'username' e 'password'. #Pegamos os dados pelos 'names' dos inputs no HTML.
        email_form = request.POST.get('username')
        senha_form = request.POST.get('password')
        
        # Verifica as credenciais: a função authenticate transforma a senha em hash e compara com o hash salvo no banco.
        user = authenticate(request, username=email_form, password=senha_form)
        
        # Se deu certo, cria a Sessão
        if user is not None:
            login(request, user)
            return redirecionar_por_tipo(user)
        else: 
            # Feedback visual de erro
            messages.error(request, 'Usuário ou senha inválidos.')
            
    return render(request, 'registration/login.html')

def cadastro_usuario(request):
    # Se o cara já está logado, chuta ele pro painel (não faz sentido cadastrar de novo)
    if request.user.is_authenticated:
        return redirecionar_por_tipo(request.user)
    
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            # O método save() que criamos no forms.py faz toda a mágica do banco
            user = form.save()
            # Já logamos o usuário automaticamente após o cadastro 
            login(request, user)
            
            messages.success(request, f'Bem-vindo, {user.first_name}! Cadastro realizado.')
            return redirecionar_por_tipo(user)
        else:
            messages.error(request, 'Erro no cadastro. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
        
    return render(request, 'registration/cadastro.html', {'form': form})

def logout_view(request):
    """
    Encerra a sessão de forma segura.
    Limpa os cookies de autenticação do navegador.
    """
    logout(request)
    return redirect('home_publica')

# ==============================================================================
# 2. ÁREA DO PRODUTOR
# ==============================================================================

@login_required # Decorador barra que não está logado
def home_produtor(request):
    # Segurança extra: mesmo logado, verificamos: "Você é realmente um produtor?"
    if request.user.tipo_usuario != 'produtor':
        messages.error(request, 'Área restrita somente para produtores.')
        return redirect('home_publica')
    
    # Filtra produtos que o dono é o usuário logado (request.user)
    produtos = Produtos.objects.filter(usuario=request.user)
    
    # Métricas para o Dashboard:
    total_produtos = produtos.count()
    # Filtro Relacional (__): "Busque certificações onde o produto do usuário é X"
    pendentes = Certificacoes.objects.filter(produto__usuario=request.user, status_certificacao='pendente').count()
    aprovados = Certificacoes.objects.filter(produto__usuario=request.user, status_certificacao='aprovado').count()
        
    # RECUPERAÇÃO DE DADOS EXTRAS DO PERFIL: Tentamos acessar a tabela 'ProdutorPerfil' vinculada.
    try:
        # ATENÇÃO: Certifique-se que no models.py o related_name é 'produtor_perfil'
        # 'produtor_perfil' é o related_name que definimos no models.py
        perfil = request.user.produtor_perfil
        nome_exibicao = perfil.nome  # Pegamos o nome da fazenda/produtor
    except:
        # Fallback caso o perfil não tenha sido criado ou o nome esteja diferente
        nome_exibicao = request.user.first_name or request.user.username
        
    contexto = {
        'produtos': produtos,
        'total_produtos': total_produtos,
        'pendentes': pendentes,
        'aprovados': aprovados,
        'usuario_nome': nome_exibicao,
    }
    
    return render(request, 'home_produtor.html', contexto)

@login_required
def cadastro_produto(request):
    # Verificação de segurança de novo, o cara tem que ser quem diz ser para poder bagunçar as coisas aqui. Não é assim não, fi!
    if request.user.tipo_usuario != 'produtor':
        return redirect('home_publica') 
    
    if request.method == 'POST':
        # Carregamos o form com os dados (POST) e arquivos de imagem (FILES)
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            # Cria o objeto na memória RAM, mas não manda pro banco ainda.
            produto = form.save(commit=False)
            # Vincula ao usuário logado (request.user)
            produto.usuario = request.user
            produto.status_estoque = 'disponivel'
            # Agora que sabemos quem é o usuário, podemos salvar no banco.
            produto.save()
            messages.success(request, f'O produto {produto.nome} foi cadastrado')
            return redirect('home_produtor')
    else:
        # Se for GET (abrir a página), entregamos um form vazio para o cara preencher.
        form = ProdutoForm()
        
    return render(request, 'cadastro_produto.html', {'form': form}) 

@login_required
def enviar_autodeclaracao(request):
    # Garantir é sempre bom =)
    if request.user.tipo_usuario != 'produtor':
        return redirect('home_publica')
    
    # Processando o formulário
    if request.method == 'POST':
        form = ProdutoComAutodeclaracaoForm(request.POST, request.FILES)
        # Filtra o dropdown para mostrar só produtos do usuário logado
        form.fields['produto'].queryset = Produtos.objects.filter(usuario=request.user)
        
        if form.is_valid():
            # Extraímos os dados limpos
            produto_selecionado = form.cleaned_data['produto']
            texto = form.cleaned_data['texto_autodeclaracao']
            arquivo = form.cleaned_data['arquivo_autodeclaracao']
            
            # Criamos manualmente o registro na tabela de Certificações
            nova_certificacao = Certificacoes(
                produto=produto_selecionado,
                texto_autodeclaracao=texto,
                documento=arquivo,
                status_certificacao='pendente', # Nasce pendente
                admin_responsavel=None, # Ninguém auditou ainda
            )
            
            nova_certificacao.save()
            messages.success(request, 'Documento enviado com sucesso! Aguardo a análise do auditor')            
            return redirect('home_produtor')
    else:
        form = ProdutoComAutodeclaracaoForm()
        # Filtra produtos no GET também
        form.fields['produto'].queryset = Produtos.objects.filter(usuario=request.user)
        
    contexto = {
        'form': form,
        'usuario_nome': request.user.first_name or request.user.username
    }
    
    return render(request, 'enviar_autodeclaracao.html', contexto)

@login_required
def deletar_produto(request, produto_id):
    # Busca o produto ou erro 404 se não existir
    produto = get_object_or_404(Produtos, id_produto=produto_id)
    
    # Verificamos se o dono do produto no banco é IGUAL a quem está tentando apagar.
    if produto.usuario != request.user:
        messages.error(request, 'Tentativa de exclusão falha. Você não é o dono do produto!')
        return redirect('home_produtor') 

    # INTEGRIDADE REFERENCIAL (Cascata Manual):
    # Antes de apagar o Pai (Produto), verificamos se tem Filhos (Certificações).
    certificacoes_vinculadas = Certificacoes.objects.filter(produto_id=produto_id)
    if certificacoes_vinculadas.exists():
        qtde = certificacoes_vinculadas.count()
        certificacoes_vinculadas.delete()
        print(f'Sistema: {qtde} certificações deletadas em cascata')
    
    # Agora é seguro apagar o pai
    nome_produto = produto.nome 
    produto.delete()
    messages.success(request, f'Produto: {nome_produto} removido!')   
    return redirect('home_produtor')

# ==============================================================================
# 3. ÁREA DA EMPRESA
# ==============================================================================

@login_required
def home_empresa(request):
    # Bloqueia quem não é empresa
    if request.user.tipo_usuario != 'empresa':
         return redirect('login')
    # Renderiza o dashboard da empresa 
    return render(request, 'home_empresa.html')

# ==============================================================================
# 4. ÁREA DO AUDITOR (ADMIN)
# ==============================================================================

@login_required
def home_admin(request):
    # Permite apenas 'auditor' 
    if request.user.tipo_usuario != 'auditor' and not request.user.is_superuser:
        messages.error(request, 'Acesso restrito a desenvolvedores!')
        return redirect('home_publica')
    
    # O auditor vê os dados de TODOS os produtores, por isso não filtramos por usuário aqui.
    pendente = Certificacoes.objects.filter(status_certificacao='pendente').count()
    aprovado = Certificacoes.objects.filter(status_certificacao='aprovado').count()
    reprovado = Certificacoes.objects.filter(status_certificacao='reprovado').count()
    
    contexto = {
        'pendente': pendente,
        'aprovado': aprovado,
        'reprovado': reprovado,
        'usuario_nome': request.user.username,
    }
    return render(request, 'home_admin.html', contexto)

@login_required
def admin_visualizar_certificados(request):
    # Verificação de Permissão
    if request.user.tipo_usuario != 'auditor' and not request.user.is_superuser:
        return redirect('login')
    # Filtro via URL (ex: ?status=pendente)
    status_filtro = request.GET.get('status')
    # O Django faz um JOIN no SQL para trazer os dados do Produto e do Produtor na mesma consulta.
    consulta = Certificacoes.objects.select_related('produto', 'produto__usuario').all().order_by('-data_envio')
    
    if status_filtro: 
        consulta = consulta.filter(status_certificacao=status_filtro)

    contexto = {
        'certificacoes': consulta,
        'status_filtro': status_filtro,
        'usuario_nome': request.user.username,
    }
    
    return render(request, 'admin_certificacoes.html', contexto)

@login_required
def admin_responder_certificacoes(request, certificacao_id):
    # Segurança mais um vez.
    if request.user.tipo_usuario != 'auditor' and not request.user.is_superuser:
        return redirect('login')
    
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao') # Captura qual botão foi clicado (Aprovar/Rejeitar)
        # Salva o usuário logado como responsável
        # Em vez de salvar só o ID, salvamos o OBJETO do usuário logado.
        admin_responsavel = request.user
        
        if acao == 'aprovar':
            certificacao.status_certificacao = 'aprovado'
            messages.success(request, f'Certificação APROVADA para o produto {certificacao.produto.nome}!')
        elif acao == 'rejeitar':
            # Usando 'reprovado' conforme seu código anterior
            certificacao.status_certificacao = 'reprovado'
            messages.warning(request, f'Certificação REJEITADA para o produto {certificacao.produto.nome}.')
        
        # Registrando o rastro da auditoria (Quem e Quando)
        certificacao.data_resposta = datetime.now().date()
        certificacao.admin_responsavel = admin_responsavel
        # Persistindo no Banco de Dados
        certificacao.save()
        
        return redirect('admin_visualizar_certificados') 
    
    return redirect('home_admin')