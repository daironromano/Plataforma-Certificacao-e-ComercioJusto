from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime

# Importamos a classe Usuarios que acabou de ser criada no models.py
from .models import Usuarios, Produtos, Certificacoes
from .forms import ProdutoComAutodeclaracaoForm, CertificacaoForm

# Função para fazer login no sistema
def login_usuarios(request):
    msg = None
    if request.method == 'POST':
        # Pega os dados do formulário HTML
        email_form = request.POST.get('email')
        senha_form = request.POST.get('senha')
        
        try:
            # Procura um usuario onde o email e a senha correspondem com o formulário
            usuario = Usuarios.objects.get(email=email_form, senha=senha_form)
            
            # SUCESSO! Salva os dados na "sessão" (memória do navegador)
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_tipo'] = usuario.tipo
            request.session['usuario_nome'] = usuario.nome
            
            # Redirecionamento baseado no tipo de usuário
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
    
    # Buscar produtos do produtor
    usuario_id = request.session.get('usuario_id')
    produtos = Produtos.objects.filter(usuario_id=usuario_id)
    
    # Buscar certificações do produtor
    certificacoes_pendentes = Certificacoes.objects.filter(
        produto__usuario_id=usuario_id,
        status_certificacao='pendente'
    ).count()
    
    certificacoes_aprovadas = Certificacoes.objects.filter(
        produto__usuario_id=usuario_id,
        status_certificacao='aprovado'
    ).count()
    
    context = {
        'produtos': produtos,
        'total_produtos': produtos.count(),
        'certificacoes_pendentes': certificacoes_pendentes,
        'certificacoes_aprovadas': certificacoes_aprovadas,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    
    return render(request, 'home_produtor.html', context)

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
    
    # Buscar todas as certificações
    todas_certificacoes = Certificacoes.objects.select_related('produto', 'produto__usuario').all()
    
    # Estatísticas
    total_certificacoes = todas_certificacoes.count()
    pendentes = todas_certificacoes.filter(status_certificacao='pendente').count()
    aprovadas = todas_certificacoes.filter(status_certificacao='aprovado').count()
    rejeitadas = todas_certificacoes.filter(status_certificacao='rejeitado').count()
    
    # Certificações recentes (últimas 10 pendentes)
    certificacoes_recentes = todas_certificacoes.filter(
        status_certificacao='pendente'
    ).order_by('-data_envio')[:10]
    
    context = {
        'total_certificacoes': total_certificacoes,
        'pendentes': pendentes,
        'aprovadas': aprovadas,
        'rejeitadas': rejeitadas,
        'certificacoes_recentes': certificacoes_recentes,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    
    return render(request, 'home_admin.html', context)

@verificar_autenticacao
def home_padrao(request):
    """
    Página padrão de início para usuários autenticados.
    """
    context = {
        'usuario_nome': request.session.get('usuario_nome'),
        'usuario_tipo': request.session.get('usuario_tipo'),
    }
    return render(request, 'home.html', context)

# Função para deslogar o usuário
def logout_view(request):
    # Limpa a sessão (desloga)
    request.session.flush()
    return redirect('login')

# ===== FUNÇÕES DE UPLOAD DE AUTODECLARAÇÃO =====

@verificar_autenticacao
def enviar_autodeclaracao(request):
    """
    View para o produtor enviar a autodeclaração de um produto.
    Permite upload de arquivo e/ou texto da autodeclaração.
    """
    # Segurança extra: Garante que só PRODUTOR entra aqui
    if request.session.get('usuario_tipo') != 'produtor':
        messages.error(request, 'Acesso negado. Apenas produtores podem enviar autodeclaração.')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuarios, id_usuario=usuario_id)
    
    # Buscar apenas produtos do produtor logado
    produtos_produtor = Produtos.objects.filter(usuario=usuario)
    
    if request.method == 'POST':
        form = ProdutoComAutodeclaracaoForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                produto = form.cleaned_data['produto']
                texto_autodeclaracao = form.cleaned_data.get('texto_autodeclaracao', '')
                arquivo_autodeclaracao = form.cleaned_data.get('arquivo_autodeclaracao')
                
                # Verificar se o produto pertence ao produtor logado
                if produto.usuario_id != usuario_id:
                    messages.error(request, 'Você não tem permissão para cadastrar certificação neste produto.')
                    return redirect('enviar_autodeclaracao')
                
                # Criar a certificação
                certificacao = Certificacoes.objects.create(
                    produto=produto,
                    texto_autodeclaracao=texto_autodeclaracao,
                    arquivo_autodeclaracao=arquivo_autodeclaracao,
                    documento=arquivo_autodeclaracao.name if arquivo_autodeclaracao else 'texto',
                    status_certificacao='pendente',
                    data_envio=datetime.now().date(),
                    admin_responsavel=None
                )
                
                messages.success(
                    request,
                    f'Autodeclaração enviada com sucesso! Sua solicitação está em análise.'
                )
                return redirect('ver_certificacoes')
                
            except Exception as e:
                messages.error(request, f'Erro ao enviar autodeclaração: {str(e)}')
        else:
            # Exibir erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProdutoComAutodeclaracaoForm()
        # Filtrar apenas produtos do usuário logado
        form.fields['produto'].queryset = produtos_produtor
    
    context = {
        'form': form,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    return render(request, 'enviar_autodeclaracao.html', context)


@verificar_autenticacao
def ver_certificacoes(request):
    """
    View para o produtor visualizar suas certificações e autodeclarações enviadas.
    """
    # Segurança extra: Garante que só PRODUTOR entra aqui
    if request.session.get('usuario_tipo') != 'produtor':
        messages.error(request, 'Acesso negado. Apenas produtores podem visualizar certificações.')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    
    # Buscar certificações dos produtos do produtor
    produtos_produtor = Produtos.objects.filter(usuario_id=usuario_id)
    certificacoes = Certificacoes.objects.filter(produto__in=produtos_produtor).order_by('-data_envio')
    
    # Adicionar flag para cada certificação indicando se o arquivo existe
    for cert in certificacoes:
        if cert.arquivo_autodeclaracao:
            try:
                # Verificar se o arquivo físico existe
                cert.arquivo_existe = cert.arquivo_autodeclaracao.storage.exists(cert.arquivo_autodeclaracao.name)
            except:
                cert.arquivo_existe = False
        else:
            cert.arquivo_existe = False
    
    context = {
        'certificacoes': certificacoes,
        'usuario_nome': request.session.get('usuario_nome'),
    }
    return render(request, 'ver_certificacoes.html', context)


@verificar_autenticacao
def baixar_arquivo_certificacao(request, certificacao_id):
    """
    View para permitir o download do arquivo de autodeclaração.
    """
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    
    # Verificar permissão: o usuário deve ser o dono do produto
    usuario_id = request.session.get('usuario_id')
    if certificacao.produto.usuario_id != usuario_id and request.session.get('usuario_tipo') != 'admin':
        messages.error(request, 'Você não tem permissão para acessar este arquivo.')
        return redirect('login')
    
    if certificacao.arquivo_autodeclaracao:
        arquivo = certificacao.arquivo_autodeclaracao.open('rb')
        response = HttpResponse(arquivo.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{certificacao.arquivo_autodeclaracao.name}"'
        return response
    else:
        messages.warning(request, 'Esta certificação não possui arquivo anexado.')
        return redirect('ver_certificacoes')


@verificar_autenticacao
def admin_visualizar_certificacoes(request):
    """
    View para admin visualizar todas as certificações enviadas.
    """
    # Segurança: Garante que só ADMIN entra aqui
    if request.session.get('usuario_tipo') != 'admin':
        messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
        return redirect('login')
    
    # Buscar todas as certificações, ordenadas por data
    certificacoes = Certificacoes.objects.select_related('produto', 'produto__usuario', 'admin_responsavel').order_by('-data_envio')
    
    # Filtro por status se fornecido
    status_filtro = request.GET.get('status')
    if status_filtro:
        certificacoes = certificacoes.filter(status_certificacao=status_filtro)
    
    context = {
        'certificacoes': certificacoes,
        'usuario_nome': request.session.get('usuario_nome'),
        'status_filtro': status_filtro,
    }
    return render(request, 'admin_certificacoes.html', context)


@verificar_autenticacao
def admin_responder_certificacao(request, certificacao_id):
    """
    View para admin aprovar/rejeitar uma certificação.
    Atualiza o status para 'aprovado' ou 'rejeitado' e registra a data e admin.
    """
    # Segurança: Garante que só ADMIN entra aqui
    if request.session.get('usuario_tipo') != 'admin':
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    certificacao = get_object_or_404(Certificacoes, id_certificacao=certificacao_id)
    usuario_admin_id = request.session.get('usuario_id')
    
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
        'usuario_nome': request.session.get('usuario_nome'),
    }
    return render(request, 'admin_responder_certificacao.html', context)

# Função para cadastrar novo usuário

# Função para adicionar certificação ao produto

# Função para adicionar produtos

# Função para empresa comprar produtos de produtor

