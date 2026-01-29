from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
# Importamos as classes que criamos no models.py
from .models import (
    UsuariosLegado, Produtos, Certificacoes, Produtor, Empresa,
    Carrinho, ItemCarrinho, Pedido, ItemPedido, CustomUser, EmpresaProdutor
)

# Importar autenticação do Django e redriecionamento
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404

# Importamos as classes de formulário
from .forms import (
    CadastroProdutorForm,
    CadastroEmpresaForm,
    UsuarioBaseConfigForm,
    ProdutorConfigForm,
    EmpresaConfigForm,
    ProdutoForm,
    EditarPerfilProdutorForm,
    EditarPerfilEmpresaForm,
    CertificacaoForm,
    CertificacaoMultiplaForm
)
# Importamos datetime
from datetime import datetime
# Importar modulo de alerta sucesso ou erro
from django.contrib import messages
# Nossos modelos (As tabelas do Banco de Dados)
from .models import Produtos, Certificacoes, Produtor, EmpresaProdutor
# Nossos formulários (A validação dos dados que entram)
from .forms import ProdutoForm, EditarPerfilProdutorForm
# Utilitários (ferramentas úteis para data e contagem)
from django.db.models import Count
# Google OAuth imports
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.helpers import complete_social_login
# Importar decoradores customizados de segurança
from .decorators import (
    user_is_produtor, 
    user_is_empresa, 
    user_is_admin,
    owns_produto,
    owns_certificacao,
    get_usuario_session
)
# ==============================================================================
# Requisições HTTP para API de CNPJ
import requests
import re
from django.utils import timezone

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

def get_user_tipo(user):
    """
    Função auxiliar para obter o tipo de usuário de forma segura.
    CustomUser agora É o modelo de autenticação, então o campo 'tipo' está diretamente no user.
    Retorna None se o usuário não estiver autenticado ou não tiver o campo.
    """
    if hasattr(user, 'tipo'):
        return user.tipo
    return None

def redirecionar_por_tipo(user):
    """
    Função auxiliar que decide para onde o usuário vai após login.
    Baseado no tipo de usuário (produtor, empresa, admin).
    Centraliza a lógica de redirecionamento.
    """
    if not user.is_authenticated:
        return redirect('login')
    
    tipo = get_user_tipo(user)
    
    if tipo == 'produtor':
        return redirect('home_produtor')
    elif tipo == 'empresa':
        return redirect('home_empresa')
    elif tipo == 'admin':
        return redirect('home_admin')
    elif user.is_superuser:
        return redirect('/admin/')
    else:
        return redirect('home_publica')

def _validar_cnpj_api_interno(cnpj):
    """
    Função auxiliar: Valida CNPJ usando API pública do ReceitaWS.
    Retorna dict com sucesso e dados ou None se inválido.
    Sistema rigoroso contra perfis falsos.
    """
    # Remove formatação do CNPJ
    cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
    
    if len(cnpj_numeros) != 14:
        return {'sucesso': False, 'erro': 'CNPJ deve ter 14 dígitos'}
    
    try:
        # API pública gratuita da ReceitaWS
        url = f'https://receitaws.com.br/v1/cnpj/{cnpj_numeros}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se o CNPJ existe e está ativo
            if dados.get('status') == 'OK':
                return {
                    'sucesso': True,
                    'razao_social': dados.get('nome', ''),
                    'nome_fantasia': dados.get('fantasia', ''),
                    'cnpj': dados.get('cnpj', ''),
                    'endereco': f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
                    'cidade': dados.get('municipio', ''),
                    'estado': dados.get('uf', ''),
                    'cep': dados.get('cep', ''),
                    'telefone': dados.get('telefone', ''),
                    'email': dados.get('email', ''),
                    'situacao': dados.get('situacao', '')
                }
            else:
                return {'sucesso': False, 'erro': 'CNPJ não encontrado na Receita Federal'}
        else:
            return {'sucesso': False, 'erro': 'Erro ao consultar API da Receita Federal'}
            
    except requests.exceptions.Timeout:
        return {'sucesso': False, 'erro': 'Tempo limite de consulta excedido'}
    except Exception as e:
        return {'sucesso': False, 'erro': f'Erro ao validar CNPJ: {str(e)}'}


# Função para fazer login no sistema


# --- View para escolher tipo de cadastro ---
def escolher_tipo_cadastro(request):
    """Tela inicial de cadastro onde o usuário escolhe: Produtor ou Empresa"""
    return render(request, 'registration/escolher_tipo.html')


def escolher_tipo_apos_google(request):
    """
    Permite que usuário escolha tipo (Produtor/Empresa) após login com Google.
    Esta view é chamada quando um novo usuário faz login via Google OAuth.
    """
    adapter = get_adapter(request)
    sociallogin = adapter.unstash_sociallogin(request)

    # Se não houver sociallogin em sessão, fluxo expirou
    if sociallogin is None and 'google_data' not in request.session:
        messages.warning(request, 'Sessão expirada. Por favor, faça login novamente.')
        return redirect('login')

    # Dados para mostrar na tela
    google_data = request.session.get('google_data', {})
    if sociallogin:
        extra = sociallogin.account.extra_data
        google_data = {
            'nome': extra.get('name', google_data.get('nome', 'Usuário')),
            'email': extra.get('email', google_data.get('email', '')),
            'picture': extra.get('picture', google_data.get('picture', '')),
        }

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo in ['produtor', 'empresa']:
            request.session['tipo_usuario_social'] = tipo

            # Se temos o sociallogin armazenado, completamos o login
            if sociallogin:
                response = complete_social_login(request, sociallogin)
                adapter.clear_stashed_sociallogin(request)
                return response
            messages.warning(request, 'Sessão expirada. Por favor, tente novamente.')
            return redirect('login')
        messages.error(request, 'Tipo de usuário inválido.')

    return render(request, 'registration/escolher_tipo_google.html', {
        'nome': google_data.get('nome', 'Usuário'),
        'email': google_data.get('email', ''),
        'picture': google_data.get('picture', '')
    })


# --- View para cadastro de Produtor ---


# --- View para cadastro de Empresa ---
           
#Função para fazer login no sistema
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
        # Pega os dados do formulário HTML (name="username" e name="password")
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
            
            messages.success(request, f'Bem-vindo, {user.nome}! Cadastro realizado.')
            return redirecionar_por_tipo(user)
        else:
            messages.error(request, 'Erro no cadastro. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
        
    return render(request, 'registration/cadastro.html', {'form': form})

def escolher_tipo_cadastro(request):
    """
    Página para escolher o tipo de cadastro (Produtor ou Empresa).
    """
    return render(request, 'escolher_tipo.html')


def escolher_tipo_apos_google(request):
    """
    Página para escolher o tipo após autenticação com Google.
    """
    return render(request, 'escolher_tipo.html')


def cadastro_produtor(request):
    """
    Cadastro específico para Produtor.
    Cria CustomUser + Produtor profile.
    """
    if request.user.is_authenticated:
        return redirecionar_por_tipo(request.user)
    
    if request.method == 'POST':
        form = CadastroProdutorForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                # Autentica o usuário
                auth_login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Bem-vindo, {usuario.nome}! Cadastro de Produtor realizado com sucesso.')
                return redirecionar_por_tipo(usuario)
            except Exception as e:
                if 'Duplicate entry' in str(e) and 'cpf' in str(e):
                    messages.error(request, 'CPF já está em uso, tente outro.')
                else:
                    messages.error(request, 'Erro ao criar cadastro. Tente novamente.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CadastroProdutorForm()
        
    return render(request, 'registration/cadastro_produtor.html', {'form': form})


def cadastro_empresa(request):
    """
    Cadastro específico para Empresa.
    Cria CustomUser + EmpresaProdutor profile.
    """
    if request.user.is_authenticated:
        return redirecionar_por_tipo(request.user)
    
    if request.method == 'POST':
        form = CadastroEmpresaForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                # Autentica o usuário
                auth_login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Bem-vindo, {usuario.nome}! Cadastro de Empresa realizado com sucesso.')
                return redirecionar_por_tipo(usuario)
            except Exception as e:
                if 'Duplicate entry' in str(e) and 'cnpj' in str(e):
                    messages.error(request, 'CNPJ já está em uso, tente outro.')
                else:
                    messages.error(request, 'Erro ao criar cadastro. Tente novamente.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CadastroEmpresaForm()
        
    return render(request, 'registration/cadastro_empresa.html', {'form': form})


def logout_view(request):
    """
    Encerra a sessão de forma segura.
    Limpa os cookies de autenticação do navegador e redireciona para home.
    """
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso!')
    return redirect('home_publica')

# ==============================================================================
# 2. ÁREA DO PRODUTOR
# ==============================================================================


# --- Função de Segurança (Decorador) ---
# Aplicar @login_required e validação de grupo em views protegidas
def verificar_autenticacao(view_func):
    """
    Decorador LEGADO mantido por compatibilidade.
    Novo código deve usar @login_required + @user_is_produtor/@user_is_empresa/@user_is_admin
    """
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_is_produtor(view_func):
    """Decorador para verificar se o usuário é um produtor."""
    def wrapper(request, *args, **kwargs):
        if get_user_tipo(request.user) != 'produtor':
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('home_publica')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_is_empresa(view_func):
    """Decorador para verificar se o usuário é uma empresa."""
    def wrapper(request, *args, **kwargs):
        if get_user_tipo(request.user) != 'empresa':
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('home_publica')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_is_admin(view_func):
    """Decorador para verificar se o usuário é um administrador."""
    def wrapper(request, *args, **kwargs):
        tipo = get_user_tipo(request.user)
        if not request.user.is_staff and tipo != 'admin':
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('home_publica')
        return view_func(request, *args, **kwargs)
    return wrapper


# --- As Telas Protegidas ---

# --- DASHBOARD DO PRODUTOR ---
@login_required(login_url='login')
@user_is_produtor

@login_required # Decorador barra que não está logado
def home_produtor(request):
    """
    Dashboard do produtor com seus produtos e certificações.
    PROTEÇÃO: @login_required + @user_is_produtor garante acesso apenas a produtores autenticados.
    IDOR Prevention: Filtra produtos apenas do usuário logado.
    """
    # Segurança: Garante que só PRODUTOR entra aqui
    if get_user_tipo(request.user) != 'produtor':
        return redirect('login')
    
    # PROTEÇÃO CONTRA IDOR: Filtra APENAS produtos do usuário logado
    produtos = Produtos.objects.filter(usuario=request.user)
    
    # Buscar certificações do produtor
    certificacoes_pendentes = Certificacoes.objects.filter(
        produto__usuario=request.user,
        status_certificacao='pendente'
    ).count()
    
    certificacoes_aprovadas = Certificacoes.objects.filter(
        produto__usuario=request.user,
        status_certificacao='aprovado'
    ).count()
    
    certificacoes_rejeitadas = Certificacoes.objects.filter(
        produto__usuario=request.user,
        status_certificacao='reprovado'
    ).count()
    
    context = {
        'produtos': produtos,
        'total_produtos': produtos.count(),
        'certificacoes_pendentes': certificacoes_pendentes,
        'certificacoes_aprovadas': certificacoes_aprovadas,
        'certificacoes_rejeitadas': certificacoes_rejeitadas,
        'usuario_nome': request.user.nome,
    }
    
    return render(request, 'home_produtor.html', context)

@login_required
def cadastro_produto(request):
    # Verificação de segurança de novo, o cara tem que ser quem diz ser para poder bagunçar as coisas aqui. Não é assim não, fi!
    if get_user_tipo(request.user) != 'produtor':
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
    return render(request, 'home_produtor.html', contexto)


@login_required
def editar_perfil_produtor(request):
    if get_user_tipo(request.user) != 'produtor':
        return redirect('home_publica')
    
    # Tenta pegar o perfil. Se não existir, cria um vazio na memória (evita crash)
    perfil, created = PerfilProduto.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = EditarPerfilProdutorForm(request.POST, request.FILES, instance=perfil)
        
        if form.is_valid():
            # 1. Salva os dados do Perfil (Bio, Nome, etc)
            form.save()
            
            # 2. Salva os dados do Usuário (Nome, Email) manualmente
            request.user.nome = form.cleaned_data['nome']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('home_produtor')
    else:
        # Carrega o formulário com os dados atuais do banco (Preenchimento automático)
        initial_data = {
            'nome': request.user.nome,
            'email': request.user.email
        }
        form = EditarPerfilProdutorForm(instance=perfil, initial=initial_data)

    return render(request, 'editar_perfil_produtor.html', {'form': form})
    
    
@login_required
@user_is_produtor
def enviar_autodeclaracao(request):
    """
    Envio de autodeclaração para certificação.
    PROTEÇÃO: @login_required + @user_is_produtor garante acesso apenas a produtores autenticados.
    IDOR Prevention: Filtra produtos apenas do usuário logado.
    """
    # Obter lista de produtos do usuário
    produtos_usuario = Produtos.objects.filter(usuario=request.user)
    
    # PROTEÇÃO CONTRA IDOR: Filtra APENAS produtos do produtor logado
    if request.method == 'POST':
        # Obter o ID do produto selecionado
        produto_id = request.POST.get('produto_id')
        
        if not produto_id:
            messages.error(request, 'Selecione um produto para enviar a certificação.')
            form = CertificacaoForm()
            return render(request, 'enviar_autodeclaracao.html', {
                'form': form,
                'usuario_nome': request.user.nome,
                'produtos': produtos_usuario
            })
        
        # Validar que o produto pertence ao usuário
        try:
            produto_selecionado = Produtos.objects.get(id_produto=produto_id, usuario=request.user)
        except Produtos.DoesNotExist:
            messages.error(request, 'Acesso negado. Este produto não pertence a você.')
            return redirect('home_produtor')
        
        form = CertificacaoForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Regra de Negócio: Criação da Certificação
            nova_certificacao = Certificacoes(
                produto=produto_selecionado,
                documento=form.cleaned_data.get('documento'),
                documento_2=form.cleaned_data.get('documento_2'),
                documento_3=form.cleaned_data.get('documento_3'),
                status_certificacao='pendente',
                data_envio=datetime.now().date(),
                admin_responsavel=None,  # Ninguém auditou ainda
            )
            
            nova_certificacao.save()
            messages.success(request, 'Documento enviado com sucesso! Aguardo a análise do auditor')            
            return redirect('home_produtor')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
    else:
        form = CertificacaoForm()
        
    contexto = {
        'form': form,
        'usuario_nome': request.user.nome,
        'produtos': produtos_usuario
    }
    
    return render(request, 'enviar_autodeclaracao.html', contexto)

# ---  Função para o produtor adicionar produtos ---
@login_required(login_url='login')
@user_is_produtor
def cadastro_produto(request):
    """
    Cadastro de novo produto.
    PROTEÇÃO: @login_required + @user_is_produtor garante acesso apenas a produtores autenticados.
    IDOR Prevention: Atribui automaticamente o dono do produto ao usuário logado.
    """
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                produto = form.save(commit=False)
                
                # PROTEÇÃO CONTRA IDOR: Define automaticamente o dono como usuário logado
                produto.usuario = request.user
                produto.status_estoque = 'disponivel'
                
                produto.save()
                messages.success(request, f'Produto "{produto.nome}" cadastrado com sucesso!')
                return redirect('home_produtor')
            except Exception as e:
                messages.error(request, f'Erro ao salvar produto: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
    else:
        form = ProdutoForm()
    
    return render(request, 'cadastro_produto.html', {'form': form})


@login_required(login_url='login')
@user_is_produtor
def deletar_produto(request, produto_id):
    """
    Deletar produto (apenas o dono pode deletar).
    PROTEÇÃO: @login_required + @user_is_produtor
    IDOR Prevention: Valida que o usuário é o dono do produto.
    """
    # PROTEÇÃO CONTRA IDOR: Filtra apenas produtos do usuário logado
    produto = get_object_or_404(Produtos, id_produto=produto_id, usuario=request.user)
    
    # Deletar certificações vinculadas em cascata
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

# --- DASHBOARD DA EMPRESA ---
@user_is_empresa
@login_required(login_url='login')
def home_empresa(request):
    """
    Dashboard da Empresa com métricas, status de verificação e alertas.
    Similar ao dashboard do produtor mas focado em dados jurídicos.
    PROTEÇÃO: @login_required garante que apenas usuários logados acessem.
    """
    # Bloqueia quem não é empresa
    if get_user_tipo(request.user) != 'empresa':
        return redirect('login')
    
    # Buscar ou criar perfil da empresa
    perfil, created = EmpresaProdutor.objects.get_or_create(
        usuario=request.user,
        defaults={
            'cnpj': '',
            'razao_social': '',
            'status_verificacao': 'pendente'
        }
    )
    
    # Verificar documentos pendentes e se os arquivos existem
    docs_pendentes = []
    doc_cnpj_existe = False
    contrato_social_existe = False
    alvara_existe = False
    
    # Verificar CNPJ
    if perfil.documento_cnpj:
        try:
            # Verifica se o arquivo existe no filesystem
            if perfil.documento_cnpj.storage.exists(perfil.documento_cnpj.name):
                doc_cnpj_existe = True
            else:
                # Campo preenchido mas arquivo não existe - limpar
                perfil.documento_cnpj = None
                perfil.save()
        except Exception:
            perfil.documento_cnpj = None
            perfil.save()
    
    if not perfil.documento_cnpj:
        docs_pendentes.append('Documento CNPJ (Cartão CNPJ)')
    
    # Verificar Contrato Social
    if perfil.documento_contrato_social:
        try:
            if perfil.documento_contrato_social.storage.exists(perfil.documento_contrato_social.name):
                contrato_social_existe = True
            else:
                perfil.documento_contrato_social = None
                perfil.save()
        except Exception:
            perfil.documento_contrato_social = None
            perfil.save()
    
    if not perfil.documento_contrato_social:
        docs_pendentes.append('Contrato Social')
    
    # Verificar Alvará de Funcionamento
    if perfil.documento_alvara:
        try:
            if perfil.documento_alvara.storage.exists(perfil.documento_alvara.name):
                alvara_existe = True
            else:
                perfil.documento_alvara = None
                perfil.save()
        except Exception:
            perfil.documento_alvara = None
            perfil.save()
    
    if not perfil.documento_alvara:
        docs_pendentes.append('Alvará de Funcionamento')
    
    # Métricas da empresa (exemplo: produtos cadastrados, pedidos, etc)
    # Aqui você pode adicionar mais métricas conforme necessidade
    total_produtos = Produtos.objects.filter(usuario=request.user).count()
    
    # Verificações de certificados (caso a empresa também tenha produtos)
    certificacoes_pendentes = Certificacoes.objects.filter(
        produto__usuario=request.user,
        status_certificacao='pendente'
    ).count()
    
    certificacoes_aprovadas = Certificacoes.objects.filter(
        produto__usuario=request.user,
        status_certificacao='aprovado'
    ).count()
    
    # Calcular progresso de documentação
    docs_enviados = 0
    if perfil.documento_cnpj:
        docs_enviados += 1
    if perfil.documento_contrato_social:
        docs_enviados += 1
    if perfil.documento_alvara:
        docs_enviados += 1
    
    progresso = int((docs_enviados / 3) * 100)
    
    contexto = {
        'perfil': perfil,
        'docs_pendentes': docs_pendentes,
        'total_docs_pendentes': len(docs_pendentes),
        'perfil_completo': len(docs_pendentes) == 0 and perfil.cnpj and perfil.razao_social,
        'total_produtos': total_produtos,
        'certificacoes_pendentes': certificacoes_pendentes,
        'certificacoes_aprovadas': certificacoes_aprovadas,
        'usuario_nome': request.user.nome,
        'progresso': progresso,
        'doc_cnpj_existe': doc_cnpj_existe,
        'contrato_social_existe': contrato_social_existe,
        'alvara_existe': alvara_existe,
    }
    
    return render(request, 'home_empresa.html', contexto)

# ==============================================================================
# 4. ÁREA DO AUDITOR (ADMIN)
# ==============================================================================

@login_required(login_url='login')
@user_is_admin
def home_admin(request):
    """
    Dashboard do administrador com estatísticas de certificações e empresas.
    PROTEÇÃO: @login_required + @user_is_admin garante acesso apenas a auditores.
    """
    
    # ===== ESTATÍSTICAS DE CERTIFICAÇÕES =====
    todas_certificacoes = Certificacoes.objects.select_related('produto', 'produto__usuario').all()
    
    total_certificacoes = todas_certificacoes.count()
    cert_pendentes = todas_certificacoes.filter(status_certificacao='pendente').count()
    cert_aprovadas = todas_certificacoes.filter(status_certificacao='aprovado').count()
    cert_rejeitadas = todas_certificacoes.filter(status_certificacao='rejeitado').count()
    
    certificacoes_recentes = todas_certificacoes.filter(
        status_certificacao='pendente'
    ).order_by('-data_envio')[:10]
    
    # ===== ESTATÍSTICAS DE EMPRESAS =====
    todas_empresas = EmpresaProdutor.objects.select_related('usuario').all()
    
    total_empresas = todas_empresas.count()
    emp_pendentes = todas_empresas.filter(status_verificacao='pendente').count()
    emp_verificadas = todas_empresas.filter(status_verificacao='verificado').count()
    emp_rejeitadas = todas_empresas.filter(status_verificacao='rejeitado').count()
    
    empresas_recentes = todas_empresas.filter(
        status_verificacao='pendente'
    ).order_by('-data_criacao')[:10]
    
    context = {
        # Certificações
        'total_certificacoes': total_certificacoes,
        'pendentes': cert_pendentes,
        'aprovadas': cert_aprovadas,
        'rejeitadas': cert_rejeitadas,
        'certificacoes_recentes': certificacoes_recentes,
        # Empresas
        'total_empresas': total_empresas,
        'emp_pendentes': emp_pendentes,
        'emp_verificadas': emp_verificadas,
        'emp_rejeitadas': emp_rejeitadas,
        'empresas_recentes': empresas_recentes,
        'usuario_nome': request.user.nome,
    }
    
    return render(request, 'home_admin.html', context)

@login_required
@user_is_admin
def admin_visualizar_certificados(request):
    # Verificação de Permissão
    tipo = get_user_tipo(request.user)
    if tipo != 'admin' and not request.user.is_superuser:
        return redirect('login')
    # Filtro via URL (ex: ?status=pendente)
    status_filtro = request.GET.get('status')
    # O Django faz um JOIN no SQL para trazer os dados do Produto e do Produtor na mesma consulta.
    consulta = Certificacoes.objects.select_related('produto', 'produto__usuario').all().order_by('-data_envio')
    
    if status_filtro: 
        consulta = consulta.filter(status_certificacao=status_filtro)
    
    return render(request, 'admin_certificacoes.html', {'certificacoes': consulta, 'status_filtro': status_filtro})

@login_required
def admin_detalhes_certificacao(request, certificacao_id):
    tipo = get_user_tipo(request.user)
    if tipo != 'admin' and not request.user.is_superuser:
        return redirect('home_publica')

    # Busca o certificado pelo ID ou dá erro 404
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    return render(request, 'admin_detalhes_certificacao.html', {'c': certificacao})

@login_required
def admin_responder_certificacoes(request, certificacao_id):
    # Segurança mais um vez.
    tipo = get_user_tipo(request.user)
    if tipo != 'admin' and not request.user.is_superuser:
        return redirect('home_publica')
    
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao') # Captura qual botão foi clicado (Aprovar/Rejeitar)
        
        if acao == 'aprovar':
            certificacao.status_certificacao = 'aprovado'
            messages.success(request, f'Certificação APROVADA para o produto {certificacao.produto.nome}!')
        elif acao == 'rejeitar':
            # Usando 'reprovado' conforme seu código anterior
            certificacao.status_certificacao = 'reprovado'
            messages.warning(request, f'Certificação REJEITADA para o produto {certificacao.produto.nome}.')
        
        # Registrando o rastro da auditoria (Quem e Quando)
        certificacao.admin_responsavel = request.user
        certificacao.data_resposta = datetime.now().date()
        certificacao.save()
        
    
    return redirect('admin_visualizar_certificacoes')

# ============================================================================
# VIEWS DE CONFIGURAÇÃO DE PERFIL
# ============================================================================

@login_required(login_url='login')
@user_is_produtor
def config_perfil_produtor(request):
    """
    View para configuração de perfil do produtor.
    Permite editar biografia, foto, contatos e redes sociais.
    """
    usuario = get_usuario_session(request)
    if not usuario:
        return redirect('login')
    
    try:
        produtor = usuario.produtor_profile
    except Produtor.DoesNotExist:
        messages.error(request, 'Perfil de produtor não encontrado.')
        return redirect('home_produtor')
    
    if request.method == 'POST':
        form_usuario = UsuarioBaseConfigForm(request.POST, instance=usuario)
        form_produtor = ProdutorConfigForm(request.POST, request.FILES, instance=produtor)
        
        if form_usuario.is_valid() and form_produtor.is_valid():
            form_usuario.save()
            form_produtor.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('config_perfil_produtor')
    else:
        form_usuario = UsuarioBaseConfigForm(instance=usuario)
        form_produtor = ProdutorConfigForm(instance=produtor)
    
    context = {
        'form_usuario': form_usuario,
        'form_produtor': form_produtor,
        'usuario': usuario,
        'produtor': produtor,
    }
    return render(request, 'produtor_config_perfil.html', context)


@login_required(login_url='login')
@user_is_empresa
def config_perfil_empresa(request):
    """
    View para configuração de perfil da empresa.
    Permite editar dados jurídicos, documentação e informações comerciais.
    Inclui validação rigorosa e integração com API de CNPJ.
    """
    usuario = get_usuario_session(request)
    if not usuario:
        return redirect('login')
    
    try:
        empresa = usuario.empresa_profile
    except Empresa.DoesNotExist:
        messages.error(request, 'Perfil de empresa não encontrado.')
        return redirect('home_empresa')
    
    if request.method == 'POST':
        form_usuario = UsuarioBaseConfigForm(request.POST, instance=usuario)
        form_empresa = EmpresaConfigForm(request.POST, request.FILES, instance=empresa)
        
        if form_usuario.is_valid() and form_empresa.is_valid():
            form_usuario.save()
            empresa_obj = form_empresa.save(commit=False)
            
            # Se CNPJ foi alterado e empresa tem documentos, marca como pendente verificação
            if 'cnpj' in form_empresa.changed_data and empresa.status_verificacao == 'verificado':
                empresa_obj.status_verificacao = 'pendente'
                messages.info(request, 'CNPJ alterado. Sua empresa será reverificada.')
            
            empresa_obj.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('config_perfil_empresa')
    else:
        form_usuario = UsuarioBaseConfigForm(instance=usuario)
        form_empresa = EmpresaConfigForm(instance=empresa)
    
    context = {
        'form_usuario': form_usuario,
        'form_empresa': form_empresa,
        'usuario': usuario,
        'empresa': empresa,
    }
    return render(request, 'empresa_config_perfil.html', context)


# ============================================================================
# VIEWS DE DETALHAMENTO PARA ADMIN (AUDITOR)
# ============================================================================

@login_required(login_url='login')
@user_is_admin
def detalhe_certificacao(request, certificacao_id):
    """
    DetailView para certificação específica.
    Mostra todas as informações detalhadas para análise do auditor.
    """
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    # Informações do produto e produtor
    produto = certificacao.produto
    produtor = produto.usuario
    
    context = {
        'certificacao': certificacao,
        'produto': produto,
        'produtor': produtor,
    }
    return render(request, 'admin_detalhe_certificacao.html', context)


@login_required(login_url='login')
@user_is_admin
def lista_certificacoes_aprovadas(request):
    """
    Lista detalhada de todas as certificações aprovadas.
    """
    certificacoes = Certificacoes.objects.filter(
        status_certificacao='aprovado'
    ).select_related('produto', 'produto__usuario', 'admin_responsavel').order_by('-data_resposta')
    
    context = {
        'certificacoes': certificacoes,
        'titulo': 'Certificações Aprovadas',
        'status_filtro': 'aprovado'
    }
    return render(request, 'admin_lista_certificacoes.html', context)


@login_required(login_url='login')
@user_is_admin
def lista_certificacoes_reprovadas(request):
    """
    Lista detalhada de todas as certificações reprovadas.
    """
    certificacoes = Certificacoes.objects.filter(
        status_certificacao='reprovado'
    ).select_related('produto', 'produto__usuario', 'admin_responsavel').order_by('-data_resposta')
    
    context = {
        'certificacoes': certificacoes,
        'titulo': 'Certificações Reprovadas',
        'status_filtro': 'reprovado'
    }
    return render(request, 'admin_lista_certificacoes.html', context)


@login_required(login_url='login')
@user_is_admin
def lista_certificacoes_pendentes(request):
    """
    Lista detalhada de todas as certificações pendentes (fila de análise).
    """
    certificacoes = Certificacoes.objects.filter(
        status_certificacao='pendente'
    ).select_related('produto', 'produto__usuario').order_by('data_envio')
    
    context = {
        'certificacoes': certificacoes,
        'titulo': 'Certificações Pendentes',
        'status_filtro': 'pendente'
    }
    return render(request, 'admin_lista_certificacoes.html', context)


# ============================================================================
# ATUALIZAÇÃO DA VIEW DE ENVIO DE AUTODECLARAÇÃO (UPLOAD MÚLTIPLO)
# ============================================================================

@login_required(login_url='login')
@user_is_produtor
def enviar_autodeclaracao_multipla(request):
    """
    View atualizada para permitir upload de até 3 documentos.
    Substitui a view antiga enviar_autodeclaracao.
    """
    usuario = get_usuario_session(request)
    if not usuario:
        return redirect('login')
    
    if request.method == 'POST':
        form = CertificacaoMultiplaForm(request.POST, request.FILES)
        form.fields['produto'].queryset = Produtos.objects.filter(usuario=usuario)
        
        if form.is_valid():
            produto_selecionado = form.cleaned_data['produto']
            texto = form.cleaned_data['texto_autodeclaracao']
            doc1 = form.cleaned_data.get('documento_1')
            doc2 = form.cleaned_data.get('documento_2')
            doc3 = form.cleaned_data.get('documento_3')
            
            # Cria a certificação
            certificacao = Certificacoes.objects.create(
                produto=produto_selecionado,
                texto_autodeclaracao=texto,
                documento=doc1,
                documento_2=doc2,
                documento_3=doc3,
                data_envio=datetime.now().date(),
                status_certificacao='pendente'
            )
            
            messages.success(request, f'Certificação enviada com sucesso para o produto "{produto_selecionado.nome}"!')
            return redirect('home_produtor')
    else:
        form = CertificacaoMultiplaForm()
        form.fields['produto'].queryset = Produtos.objects.filter(usuario=usuario)
    
    context = {
        'form': form,
        'usuario': usuario,
    }
    return render(request, 'enviar_autodeclaracao_multipla.html', context)

# ===== FUNÇÕES DE UPLOAD DE AUTODECLARAÇÃO =====
# ============================================================================
# VALIDADOR DE CNPJ COM API PÚBLICA
# ============================================================================

def validar_cnpj_api(request):
    """
    API endpoint para validar CNPJ usando API pública (ReceitaWS).
    Retorna dados da empresa se CNPJ for válido.
    Endpoint para chamadas AJAX do formulário.
    """
    cnpj = request.GET.get('cnpj', '').strip()
    
    if not cnpj:
        return JsonResponse({'valido': False, 'erro': 'CNPJ não fornecido'}, status=400)
    
    # Remove formatação
    cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
    
    if len(cnpj_numeros) != 14:
        return JsonResponse({'valido': False, 'erro': 'CNPJ deve ter 14 dígitos'}, status=400)
    
    try:
        # Consulta API pública da Receita Federal
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_numeros}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se houve erro na API
            if dados.get('status') == 'ERROR':
                return JsonResponse({
                    'valido': False,
                    'erro': f"CNPJ não encontrado ou inválido: {dados.get('message', 'Erro desconhecido')}"
                })
            
            # Sucesso - retorna dados formatados
            return JsonResponse({
                'valido': True,
                'razao_social': dados.get('nome', ''),
                'nome_fantasia': dados.get('fantasia', ''),
                'cnpj': dados.get('cnpj', ''),
                'situacao': dados.get('situacao', ''),
                'logradouro': dados.get('logradouro', ''),
                'numero': dados.get('numero', ''),
                'municipio': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cep': dados.get('cep', ''),
                'telefone': dados.get('telefone', ''),
                'email': dados.get('email', ''),
            })
        else:
            return JsonResponse({
                'valido': False,
                'erro': f'Erro ao consultar API (Status {response.status_code})'
            })
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'valido': False,
            'erro': 'Tempo limite excedido - API não respondeu'
        })
    except requests.RequestException as e:
        return JsonResponse({
            'valido': False,
            'erro': f'Erro de conexão: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'valido': False,
            'erro': f'Erro inesperado: {str(e)}'
        })


# ============================================================================
# VIEWS DE CARRINHO E CHECKOUT
# ============================================================================

@login_required(login_url='login')
@user_is_empresa
def ver_carrinho(request):
    """View para visualizar o carrinho de compras (apenas para empresas)"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem comprar produtos.')
        return redirect('home')
    
    carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, ativo=True)
    itens = carrinho.itens.all().select_related('produto')
    total = carrinho.get_total()
    quantidade_itens = carrinho.get_quantidade_itens()
    
    context = {
        'carrinho': carrinho,
        'itens': itens,
        'total': total,
        'quantidade_itens': quantidade_itens,
    }
    
    return render(request, 'carrinho.html', context)


@login_required(login_url='login')
@user_is_empresa
def adicionar_ao_carrinho(request, produto_id):
    """View para adicionar produto ao carrinho (apenas para empresas)"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem comprar produtos.')
        return redirect('home')
    
    produto = get_object_or_404(Produtos, id_produto=produto_id)
    
    if produto.status_estoque != 'disponivel':
        messages.error(request, 'Este produto não está disponível no momento.')
        return redirect('listagem_produtos')
    
    carrinho, created = Carrinho.objects.get_or_create(usuario=request.user, ativo=True)
    
    item, created = ItemCarrinho.objects.get_or_create(
        carrinho=carrinho,
        produto=produto,
        defaults={'preco_unitario': produto.preco, 'quantidade': 1}
    )
    
    if not created:
        item.quantidade += 1
        item.save()
        messages.success(request, f'Quantidade de {produto.nome} atualizada no carrinho!')
    else:
        messages.success(request, f'{produto.nome} adicionado ao carrinho!')
    
    return redirect('ver_carrinho')


@login_required(login_url='login')
@user_is_empresa
def remover_do_carrinho(request, item_id):
    """View para remover item do carrinho"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem comprar produtos.')
        return redirect('home')
    
    item = get_object_or_404(ItemCarrinho, pk=item_id, carrinho__usuario=request.user)
    produto_nome = item.produto.nome
    item.delete()
    
    messages.success(request, f'{produto_nome} removido do carrinho!')
    return redirect('ver_carrinho')


@login_required(login_url='login')
@user_is_empresa
def atualizar_quantidade_carrinho(request, item_id):
    """View para atualizar quantidade de um item no carrinho"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem comprar produtos.')
        return redirect('home')
    
    if request.method == 'POST':
        item = get_object_or_404(ItemCarrinho, pk=item_id, carrinho__usuario=request.user)
        nova_quantidade = int(request.POST.get('quantidade', 1))
        
        if nova_quantidade > 0:
            item.quantidade = nova_quantidade
            item.save()
            messages.success(request, 'Quantidade atualizada!')
        else:
            item.delete()
            messages.success(request, 'Item removido do carrinho!')
    
    return redirect('ver_carrinho')


@login_required(login_url='login')
@user_is_empresa
def checkout(request):
    """View para página de checkout (apenas para empresas)"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem comprar produtos.')
        return redirect('home')
    
    carrinho = get_object_or_404(Carrinho, usuario=request.user, ativo=True)
    itens = carrinho.itens.all().select_related('produto')
    
    if not itens:
        messages.warning(request, 'Seu carrinho está vazio!')
        return redirect('listagem_produtos')
    
    total = carrinho.get_total()
    
    if request.method == 'POST':
        # Validação dos dados de entrega
        endereco = request.POST.get('endereco', '').strip()
        cidade = request.POST.get('cidade', '').strip()
        estado = request.POST.get('estado', '').strip()
        cep = request.POST.get('cep', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        metodo_pagamento = request.POST.get('metodo_pagamento', '').strip()
        
        if not all([endereco, cidade, estado, cep, telefone, metodo_pagamento]):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        else:
            # Criar pedido
            pedido = Pedido.objects.create(
                usuario=request.user,
                total=total,
                endereco_entrega=endereco,
                cidade_entrega=cidade,
                estado_entrega=estado,
                cep_entrega=cep,
                telefone_contato=telefone,
                metodo_pagamento=metodo_pagamento,
                observacoes=request.POST.get('observacoes', '')
            )
            
            # Criar itens do pedido
            for item in itens:
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=item.produto,
                    quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario,
                    subtotal=item.get_subtotal()
                )
            
            # Limpar carrinho
            carrinho.ativo = False
            carrinho.save()
            
            messages.success(request, f'Pedido #{pedido.pk} realizado com sucesso!')
            return redirect('detalhes_pedido', pedido_id=pedido.pk)
    
    context = {
        'carrinho': carrinho,
        'itens': itens,
        'total': total,
        'usuario_nome': request.user.nome,
    }
    return render(request, 'checkout.html', context)


# ==============================================================================
# VIEWS ADICIONAIS - ÁREA DO PRODUTOR
# ==============================================================================

@login_required(login_url='login')
@user_is_produtor
def enviar_autodeclaracao_multipla(request):
    """
    Permite enviar autodeclaração para múltiplos produtos de uma vez.
    Suporta até 3 arquivos conforme especificação.
    """
    if request.method == 'POST':
        produtos_ids = request.POST.getlist('produtos')
        texto = request.POST.get('texto_autodeclaracao', '')
        arquivo1 = request.FILES.get('arquivo_1')
        arquivo2 = request.FILES.get('arquivo_2')
        arquivo3 = request.FILES.get('arquivo_3')
        
        if not produtos_ids:
            messages.error(request, 'Selecione pelo menos um produto.')
            return redirect('enviar_autodeclaracao_multipla')
        
        # Criar certificação para cada produto selecionado
        count = 0
        for produto_id in produtos_ids:
            try:
                produto = Produtos.objects.get(id_produto=produto_id, usuario=request.user)
                
                # Criar certificação
                cert = Certificacoes.objects.create(
                    produto=produto,
                    texto_autodeclaracao=texto,
                    arquivo_autodeclaracao=arquivo1 or arquivo2 or arquivo3,
                    status_certificacao='pendente',
                    data_envio=datetime.now().date()
                )
                count += 1
            except Produtos.DoesNotExist:
                continue
        
        if count > 0:
            messages.success(request, f'{count} autodeclaração(ões) enviada(s) com sucesso!')
        else:
            messages.error(request, 'Nenhuma autodeclaração foi criada.')
        
        return redirect('home_produtor')
    
    # GET - mostrar formulário
    produtos = Produtos.objects.filter(usuario=request.user, status_estoque='disponivel')
    return render(request, 'enviar_autodeclaracao_multipla.html', {'produtos': produtos})


@login_required(login_url='login')
@user_is_produtor
def config_perfil_produtor(request):
    """
    Configuração do perfil do produtor (Bio, Contato, Endereço).
    """
    # Buscar ou criar perfil
    perfil, created = Produtor.objects.get_or_create(
        usuario=request.user,
        defaults={
            'cpf': '',
            'bio': ''
        }
    )
    
    if request.method == 'POST':
        form = EditarPerfilProdutorForm(request.POST, instance=perfil)
        if form.is_valid():
            # Atualizar também dados do User
            request.user.nome = form.cleaned_data.get('nome', request.user.nome)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('home_produtor')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os campos.')
    else:
        form = EditarPerfilProdutorForm(instance=perfil, initial={
            'nome': request.user.nome,
            'email': request.user.email
        })
    
    return render(request, 'editar_perfil_produtor.html', {'form': form})


# ==============================================================================
# VIEWS ADICIONAIS - ÁREA DA EMPRESA
# ==============================================================================

@login_required(login_url='login')
@user_is_empresa
def config_perfil_empresa(request):
    """
    Configuração do perfil da empresa (CNPJ, Documentação).
    Sistema rigoroso para evitar perfis falsos usando API da Receita Federal.
    PROTEÇÃO: @login_required + validação de CNPJ via API pública.
    """
    # Bloqueia quem não é empresa
    if get_user_tipo(request.user) != 'empresa':
        return redirect('login')
    
    # Buscar ou criar perfil
    perfil, created = EmpresaProdutor.objects.get_or_create(
        usuario=request.user,
        defaults={
            'cnpj': '',
            'razao_social': '',
            'status_verificacao': 'pendente'
        }
    )
    
    if request.method == 'POST':
        form = EditarPerfilEmpresaForm(request.POST, request.FILES, instance=perfil)
        
        # DEBUG: Mostrar erros do formulário
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
            
            # Retorna o formulário com os erros
            doc_cnpj_existe = bool(perfil.documento_cnpj)
            contrato_social_existe = bool(perfil.documento_contrato_social)
            alvara_existe = bool(perfil.documento_alvara)
            
            return render(request, 'empresa_config_perfil.html', {
                'form': form, 
                'perfil': perfil,
                'documentos_completos': bool(perfil.documento_cnpj and perfil.documento_contrato_social and perfil.documento_alvara),
                'doc_cnpj_existe': doc_cnpj_existe,
                'contrato_social_existe': contrato_social_existe,
                'alvara_existe': alvara_existe,
            })
        
        if form.is_valid():
            # Pegar o CNPJ enviado
            cnpj = form.cleaned_data.get('cnpj', '')
            
            # Validar CNPJ na API da Receita Federal (sistema rigoroso)
            if cnpj and cnpj != perfil.cnpj:  # Só valida se mudou o CNPJ
                resultado_api = _validar_cnpj_api_interno(cnpj)
                
                if resultado_api['sucesso']:
                    # Preenche dados automaticamente da Receita Federal
                    perfil.razao_social = resultado_api.get('razao_social', perfil.razao_social)
                    perfil.nome_fantasia = resultado_api.get('nome_fantasia', perfil.nome_fantasia)
                    perfil.endereco = resultado_api.get('endereco', perfil.endereco)
                    perfil.cidade = resultado_api.get('cidade', perfil.cidade)
                    perfil.estado = resultado_api.get('estado', perfil.estado)
                    perfil.cep = resultado_api.get('cep', perfil.cep)
                    perfil.telefone = resultado_api.get('telefone', perfil.telefone)
                    
                    # Verifica situação cadastral
                    if resultado_api.get('situacao', '').upper() != 'ATIVA':
                        messages.warning(
                            request, 
                            f'ATENÇÃO: Situação cadastral do CNPJ: {resultado_api.get("situacao")}. '
                            'Apenas empresas ativas podem ser verificadas.'
                        )
                    
                    messages.success(
                        request, 
                        f'CNPJ validado com sucesso! Dados preenchidos automaticamente da Receita Federal.'
                    )
                else:
                    messages.error(request, f'Erro na validação: {resultado_api.get("erro")}')
                    return render(request, 'empresa_config_perfil.html', {'form': form, 'perfil': perfil})
            
            # Atualiza os dados do usuário (nome e email)
            request.user.nome = form.cleaned_data.get('nome', request.user.nome)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            
            # Salva o formulário (inclui arquivos de documentos)
            perfil_atualizado = form.save(commit=False)
            perfil_atualizado.usuario = request.user
            perfil_atualizado.data_atualizacao = timezone.now()
            perfil_atualizado.save()
            
            # Se todos os documentos foram enviados, marca como pendente de verificação
            if (perfil_atualizado.documento_cnpj and 
                perfil_atualizado.documento_contrato_social and 
                perfil_atualizado.documento_alvara):
                messages.success(
                    request,
                    '✅ Perfil atualizado com sucesso! Documentos enviados e aguardando verificação do auditor.'
                )
            else:
                messages.success(request, '✅ Perfil da empresa atualizado com sucesso!')
            
            return redirect('home_empresa')
    else:
        # Inicializa o formulário com dados do perfil e do usuário
        form = EditarPerfilEmpresaForm(
            instance=perfil,
            initial={
                'nome': request.user.nome,
                'email': request.user.email,
            }
        )
    
    # Verificar se os arquivos existem fisicamente
    doc_cnpj_existe = False
    contrato_social_existe = False
    alvara_existe = False
    
    if perfil.documento_cnpj:
        try:
            doc_cnpj_existe = perfil.documento_cnpj.storage.exists(perfil.documento_cnpj.name)
        except Exception:
            pass
    
    if perfil.documento_contrato_social:
        try:
            contrato_social_existe = perfil.documento_contrato_social.storage.exists(perfil.documento_contrato_social.name)
        except Exception:
            pass
    
    if perfil.documento_alvara:
        try:
            alvara_existe = perfil.documento_alvara.storage.exists(perfil.documento_alvara.name)
        except Exception:
            pass
    
    return render(request, 'empresa_config_perfil.html', {
        'form': form, 
        'perfil': perfil,
        'documentos_completos': bool(perfil.documento_cnpj and perfil.documento_contrato_social and perfil.documento_alvara),
        'doc_cnpj_existe': doc_cnpj_existe,
        'contrato_social_existe': contrato_social_existe,
        'alvara_existe': alvara_existe,
    })


# ==============================================================================
# VIEWS ADICIONAIS - ÁREA DO AUDITOR/ADMIN
# ==============================================================================

@login_required(login_url='login')
@user_is_admin
def detalhe_certificacao(request, certificacao_id):
    """
    Detalhe completo de uma certificação para análise do auditor.
    """
    certificacao = get_object_or_404(
        Certificacoes.objects.select_related('produto', 'produto__usuario', 'admin_responsavel'),
        id_certificacao=certificacao_id
    )
    
    context = {
        'certificacao': certificacao,
        'usuario_nome': request.user.nome,
    }
    return render(request, 'admin_detalhe_certificacao.html', context)


@login_required(login_url='login')
@user_is_admin
def lista_empresas_pendentes(request):
    """Lista empresas pendentes de verificação."""
    empresas = EmpresaProdutor.objects.filter(
        status_verificacao='pendente'
    ).select_related('usuario').order_by('-data_criacao')
    
    # Filtrar apenas empresas que enviaram todos os documentos
    empresas_completas = [
        empresa for empresa in empresas 
        if empresa.documento_cnpj and empresa.documento_contrato_social and empresa.documento_alvara
    ]
    
    return render(request, 'admin_lista_empresas.html', {
        'empresas': empresas_completas,
        'titulo': 'Empresas Pendentes de Verificação',
        'status': 'pendente',
        'status_display': 'pendentes'
    })

@login_required(login_url='login')
@user_is_admin
def lista_empresas_verificadas(request):
    """Lista empresas verificadas e aprovadas."""
    empresas = EmpresaProdutor.objects.filter(
        status_verificacao='verificado'
    ).select_related('usuario').order_by('-data_verificacao')
    
    return render(request, 'admin_lista_empresas.html', {
        'empresas': empresas,
        'titulo': 'Empresas Verificadas',
        'status': 'verificado',
        'status_display': 'verificadas'
    })

@login_required(login_url='login')
@user_is_admin
def lista_empresas_rejeitadas(request):
    """Lista empresas rejeitadas na verificação."""
    empresas = EmpresaProdutor.objects.filter(
        status_verificacao='rejeitado'
    ).select_related('usuario').order_by('-data_verificacao')
    
    return render(request, 'admin_lista_empresas.html', {
        'empresas': empresas,
        'titulo': 'Empresas Rejeitadas',
        'status': 'rejeitado',
        'status_display': 'rejeitadas'
    })


@login_required(login_url='login')
@user_is_admin
def detalhe_empresa(request, empresa_id):
    """Detalhe completo de uma empresa para verificação do admin."""
    empresa = get_object_or_404(
        EmpresaProdutor.objects.select_related('usuario'),
        id=empresa_id
    )
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        motivo = request.POST.get('motivo', '').strip()
        
        if acao == 'aprovar':
            empresa.status_verificacao = 'verificado'
            empresa.data_verificacao = timezone.now()
            empresa.observacoes_verificacao = ''
            empresa.save()
            messages.success(request, f'✅ Empresa {empresa.razao_social} verificada com sucesso!')
            return redirect('lista_empresas_verificadas')
            
        elif acao == 'reprovar':
            if not motivo:
                messages.error(request, 'Por favor, informe o motivo da reprovação.')
                return render(request, 'admin_detalhe_empresa.html', {'empresa': empresa})
            
            empresa.status_verificacao = 'rejeitado'
            empresa.data_verificacao = timezone.now()
            empresa.observacoes_verificacao = motivo
            empresa.save()
            # TODO: Enviar email para a empresa com o motivo da reprovação
            messages.warning(request, f'❌ Empresa {empresa.razao_social} rejeitada. Motivo: {motivo}')
            return redirect('lista_empresas_rejeitadas')
    
    context = {
        'empresa': empresa,
        'usuario_nome': request.user.nome,
    }
    return render(request, 'admin_detalhe_empresa.html', context)


# ==============================================================================
# CARRINHO E CHECKOUT (FUNCIONALIDADE BÁSICA)
# ==============================================================================

@login_required(login_url='login')
def meus_pedidos(request):
    """Listar pedidos do usuário logado"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem acessar pedidos.')
        return redirect('home')
    
    pedidos = Pedido.objects.filter(usuario=request.user).select_related().prefetch_related('itens__produto')
    
    context = {
        'pedidos': pedidos,
    }
    
    return render(request, 'meus_pedidos.html', context)


@login_required(login_url='login')
def detalhes_pedido(request, pedido_id):
    """Detalhes de um pedido específico"""
    if request.user.tipo != 'empresa':
        messages.error(request, 'Apenas empresas podem acessar pedidos.')
        return redirect('home')
    
    pedido = get_object_or_404(Pedido, pk=pedido_id, usuario=request.user)
    itens = pedido.itens.all().select_related('produto')
    
    context = {
        'pedido': pedido,
        'itens': itens,
    }
    
    return render(request, 'detalhes_pedido.html', context)


# ==============================================================================
# MARKETPLACE EXTERNO (IMPLEMENTAÇÃO BÁSICA)
# ==============================================================================

@login_required(login_url='login')
@user_is_produtor
def gerar_anuncio_marketplace(request, produto_id):
    """Gerar anúncio para marketplace externo."""
    produto = get_object_or_404(Produtos, id_produto=produto_id, usuario=request.user)
    
    # Gerar conteúdo básico de anúncio
    conteudo = f"""
    Produto: {produto.nome}
    Categoria: {produto.categoria}
    Preço: R$ {produto.preco}
    Descrição: {produto.descricao or 'Produto de qualidade da Amazônia'}
    """
    
    messages.success(request, f'Anúncio gerado para {produto.nome}!')
    return render(request, 'marketplace_anuncio.html', {
        'produto': produto,
        'conteudo': conteudo
    })


@login_required(login_url='login')
def visualizar_anuncio(request, anuncio_id):
    """Visualizar anúncio gerado."""
    return render(request, 'visualizar_anuncio.html', {
        'anuncio': None
    })


@login_required(login_url='login')
@user_is_produtor
def meus_anuncios(request):
    """Listar anúncios do produtor."""
    produtos = Produtos.objects.filter(usuario=request.user)
    return render(request, 'meus_anuncios.html', {
        'produtos': produtos
    })


@login_required(login_url='login')
def admin_responder_certificacao(request, certificacao_id):
    """
    View para admin aprovar/rejeitar uma certificação.
    Atualiza o status para 'aprovado' ou 'rejeitado' e registra a data e admin.
    """
    # Segurança: Garante que só ADMIN entra aqui
    if get_user_tipo(request.user) != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        comentario = request.POST.get('comentario', '')
        
        # Aceitar valores de ação
        if acao in ['aprovar', 'aprovado', 'aprovada']:
            certificacao.status_certificacao = 'aprovado'
            certificacao.data_resposta = datetime.now().date()
            certificacao.admin_responsavel_id = usuario_admin_id
            certificacao.save()
            
            messages.success(
                request, 
                f'✅ Certificação APROVADA com sucesso! Produto: {certificacao.produto.nome}'
            )
            return redirect('admin_visualizar_certificacoes')
            
        elif acao in ['rejeitar', 'rejeitado', 'rejeitada']:
            certificacao.status_certificacao = 'rejeitado'
            certificacao.data_resposta = datetime.now().date()
            certificacao.admin_responsavel_id = usuario_admin_id
            certificacao.save()
            
            messages.warning(
                request,
                f'❌ Certificação REJEITADA. Produto: {certificacao.produto.nome}'
            )
            return redirect('admin_visualizar_certificacoes')
        else:
            messages.error(request, 'Ação inválida.')
    
    context = {
        'certificacao': certificacao,
        'usuario_nome': request.user.nome,
    }
    
    return render(request, 'visualizar_anuncio.html', context)


@login_required(login_url='login')
@user_is_produtor
def meus_anuncios(request):
    """View para listar todos os anúncios do produtor"""
    usuario = get_usuario_session(request)
    if not usuario:
        return redirect('login')
    
    anuncios = Marketplace.objects.filter(produto__usuario=usuario).select_related('produto').order_by('-data_geracao')
    
    context = {
        'anuncios': anuncios,
    }
    
    return render(request, 'meus_anuncios.html', context)


# --- Função para deslogar o usuário --- (mantida por compatibilidade)
# Movida para cima no código
  
# --- Função para cadastrar novo usuário ---

# ---  Função para adicionar certificação ao produto ---

# ---  Função para empresa comprar produtos de produtor ---
