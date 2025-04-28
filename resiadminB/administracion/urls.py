from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, welcome

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)

urlpatterns = [
    path('', welcome),  # Ruta raíz
    path('', include(router.urls)),
]