from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, Certification, Category
from .serializers import (
    ProductCreateSerializer, 
    CertificationAuditSerializer, 
    CategorySerializer
)

# 1. VIEWSET DE CATEGORIAS (Auxiliar)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista as categorias para preencher os dropdowns no Frontend.
    Apenas leitura para garantir padronização.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# 2. VIEWSET DE PRODUTOS (Visão do Produtor e Vitrine)
class ProductViewSet(viewsets.ModelViewSet):
    """
    Gerencia o ciclo de vida do produto.
    - Produtores: Veem e editam apenas seus produtos.
    - Admins: Veem tudo.
    - Público: Vê apenas produtos com certificação APROVADA.
    """
    serializer_class = ProductCreateSerializer
    # Adiciona filtros de busca para facilitar o "Mapeamento" citado na ata
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category__name']
    ordering_fields = ['price', 'created_at']

    def get_permissions(self):
        # Permite leitura pública (vitrine), mas edição apenas logado
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        
        # Se for Admin, vê tudo (para suporte ou visão geral)
        if user.is_staff or (user.is_authenticated and user.type == 'ADMIN'):
            return Product.objects.all()
            
        # Se for Produtor logado, vê seus próprios produtos (Dashboard do Produtor)
        # Isso atende ao requisito de "Cadastramento" pelo produtor [cite: 30]
        if user.is_authenticated and user.type == 'PRODUTOR':
            return Product.objects.filter(producer=user)
            
        # Se for usuário anônimo ou comprador, vê apenas produtos CERTIFICADOS
        # Isso garante "vendas confiáveis" conforme o objetivo 
        return Product.objects.filter(certification__status='APPROVED')

    def perform_create(self, serializer):
        # Garante que o produto seja salvo vinculado ao usuário logado
        serializer.save(producer=self.request.user)


# 3. VIEWSET DE AUDITORIA (Exclusivo Admin)
class CertificationAuditViewSet(viewsets.GenericViewSet, 
                                viewsets.mixins.ListModelMixin,
                                viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.UpdateModelMixin):
    """
    Painel exclusivo para o Auditor (Admin) aprovar ou reprovar certificações.
    Não permite criar ou deletar certificações aqui (isso é automático no cadastro do produto).
    """
    queryset = Certification.objects.all()
    serializer_class = CertificationAuditSerializer
    permission_classes = [permissions.IsAdminUser] # Apenas Admins acessam [cite: 12]

    def get_queryset(self):
        # Por padrão, mostra primeiro os pendentes para facilitar o trabalho do auditor
        return Certification.objects.all().order_by('status', '-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Atalho para aprovar rapidamente uma certificação"""
        certification = self.get_object()
        certification.status = 'APPROVED'
        certification.auditor_notes = request.data.get('notes', 'Aprovado pelo auditor.')
        certification.validated_by = request.user
        certification.save()
        return Response({'status': 'Certificação Aprovada'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Atalho para reprovar rapidamente"""
        certification = self.get_object()
        certification.status = 'REJECTED'
        certification.auditor_notes = request.data.get('notes', 'Documentação insuficiente.')
        certification.validated_by = request.user
        certification.save()
        return Response({'status': 'Certificação Reprovada'}, status=status.HTTP_200_OK)
    
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer