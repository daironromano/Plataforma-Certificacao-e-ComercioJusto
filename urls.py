from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CertificationAuditViewSet, CategoryViewSet

# Criação automática de rotas
router = DefaultRouter()
router.register(r'produtos', ProductViewSet, basename='produto')
router.register(r'categorias', CategoryViewSet, basename='categoria')
router.register(r'auditoria', CertificationAuditViewSet, basename='auditoria')

urlpatterns = [
    path('api/', include(router.urls)),
]

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ... suas outras rotas
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView # Importe sua view customizada

urlpatterns = [
    # Rota de Login customizada (retorna tokens + type + id)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # A rota de refresh continua a padrão, pois não precisamos de dados extras nela
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ... suas outras rotas (router.urls)
]