from rest_framework import serializers
from .models import Product, Certification, Category, User

# 1. Serializer Auxiliar para Categoria (Dropdown no React)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# 2. Serializer de Certificação (Para Upload e Auditoria)
class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id', 'status', 'tech_sheet', 'invoice', 'photo_evidence', 'auditor_notes', 'validated_at']
        # O status e as notas são somente leitura para o Produtor
        read_only_fields = ['status', 'auditor_notes', 'validated_at']

# 3. Serializer de Produto (Cadastro Completo)
class ProductCreateSerializer(serializers.ModelSerializer):
    # Aninhamos o serializer de certificação para criar tudo em uma única requisição
    certification = CertificationSerializer()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 
            'stock_status', 'certification'
        ]

    def create(self, validated_data):
        # Separamos os dados da certificação dos dados do produto
        certification_data = validated_data.pop('certification')
        
        # O produtor é o usuário logado (passado via context no ViewSet)
        producer = self.context['request'].user
        
        # Criação do Produto
        product = Product.objects.create(producer=producer, **validated_data)
        
        # Criação automática da Certificação vinculada (Autodeclaração)
        Certification.objects.create(product=product, **certification_data)
        
        return product

# 4. Serializer de Auditoria (Para o Admin usar no Dashboard)
class CertificationAuditSerializer(serializers.ModelSerializer):
    # Trazemos informações do produto e do produtor para o auditor ver quem está avaliando
    product_name = serializers.CharField(source='product.name', read_only=True)
    producer_name = serializers.CharField(source='product.producer.get_full_name', read_only=True)
    
    class Meta:
        model = Certification
        fields = [
            'id', 'product_name', 'producer_name', 
            'status', 'auditor_notes', # Campos que o auditor vai editar
            'tech_sheet', 'invoice', 'photo_evidence' # Campos para visualização
        ]
        read_only_fields = ['tech_sheet', 'invoice', 'photo_evidence']

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 1. Executa a validação padrão (gera os tokens access e refresh)
        data = super().validate(attrs)

        # 2. Adiciona dados extras na resposta JSON (o React vai ler isso)
        data['type'] = self.user.type
        data['username'] = self.user.username
        data['id'] = self.user.id
        
        # Opcional: Adicionar o nome completo se quiser exibir "Olá, Fulano"
        data['full_name'] = self.user.get_full_name()

        return data