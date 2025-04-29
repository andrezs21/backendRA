from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, WhiteListViewSet, PagoViewSet, ReservaViewSet, NotificacionViewSet, welcome, PagoDetalleViewSet, GastoComunViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'whitelist', WhiteListViewSet)
router.register(r'pagos', PagoViewSet)
router.register(r'pagos-detalle', PagoDetalleViewSet)
router.register(r'gastos-comunes', GastoComunViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'notificaciones', NotificacionViewSet)

urlpatterns = [
    path('', welcome, name='welcome'),
    path('', include(router.urls)),
]