from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model, logout
from django.contrib.auth.hashers import make_password
from .models import Usuario, WhiteList, Pago, Reserva, Notificacion, PagoDetalle, GastoComun, Rol
from .serializers import UsuarioSerializer, WhiteListSerializer, PagoSerializer, ReservaSerializer, NotificacionSerializer, PagoDetalleSerializer, GastoComunSerializer
from django.http import HttpResponse

# Create your views here.

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UsuarioSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Verificar si el email está en la whitelist
            email = serializer.validated_data.get('email')
            whitelist_entry = WhiteList.objects.filter(email=email).first()
            if not whitelist_entry:
                return Response(
                    {"error": "Email no autorizado para registro"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener el rol de Residente
            rol_residente = Rol.objects.filter(nombre='RESIDENTE').first()
            if not rol_residente:
                return Response(
                    {"error": "Rol de Residente no encontrado en el sistema"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Asignar el rol de Residente usando rol_id
            serializer.validated_data['rol_id'] = rol_residente.id
            
            # Crear el usuario
            user = serializer.save()
            user.set_password(serializer.validated_data['password'])
            user.save()
            
            # Actualizar el estado de la whitelist
            whitelist_entry.estado = 'REGISTRADO'
            whitelist_entry.save()
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UsuarioSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = get_user_model().objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UsuarioSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except get_user_model().DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Sesión cerrada exitosamente"})
            return Response(
                {"error": "Token de refresh no proporcionado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Error al cerrar sesión"},
                status=status.HTTP_400_BAD_REQUEST
            )

class WhiteListViewSet(viewsets.ModelViewSet):
    queryset = WhiteList.objects.all()
    serializer_class = WhiteListSerializer
    permission_classes = [permissions.IsAuthenticated]

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'Administrador':
            return Pago.objects.all()
        # Para residentes, mostrar solo sus pagos
        return Pago.objects.filter(usuario=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                "message": "No hay pagos registrados",
                "data": []
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'Administrador':
            return Reserva.objects.all()
        # Para residentes, mostrar solo sus reservas
        return Reserva.objects.filter(usuario=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                "message": "No hay reservas registradas",
                "data": []
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol.nombre == 'Administrador':
            return Notificacion.objects.all()
        # Para residentes, mostrar solo las notificaciones donde son destinatarios
        return Notificacion.objects.filter(destinatarios=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                "message": "No hay notificaciones",
                "data": []
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PagoDetalleViewSet(viewsets.ModelViewSet):
    queryset = PagoDetalle.objects.all()
    serializer_class = PagoDetalleSerializer
    permission_classes = [permissions.IsAuthenticated]

class GastoComunViewSet(viewsets.ModelViewSet):
    queryset = GastoComun.objects.all()
    serializer_class = GastoComunSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = GastoComun.objects.all()
        mes = self.request.query_params.get('mes', None)
        anio = self.request.query_params.get('anio', None)
        
        if mes and anio:
            queryset = queryset.filter(mes=mes, anio=anio)
        
        return queryset

@api_view(['GET'])
def welcome(request):
    return HttpResponse("Bienvenido a la API de ResiAdmin")

@api_view(['POST'])
def logout_view(request):
    try:
        # Limpiar el token de refresh si existe
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Limpiar la sesión
        logout(request)
        
        return Response({
            'message': 'Sesión cerrada exitosamente'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
