from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WhiteList, Pago, Reserva, Notificacion, Rol, UnidadHabitacional, EspacioComun, ReservaDetalle, PagoDetalle, GastoComun

User = get_user_model()

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']

class UnidadHabitacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadHabitacional
        fields = ['id', 'numero', 'tipo', 'complejo', 'metros_cuadrados', 
                 'fecha_creacion', 'activo']
        read_only_fields = ['id', 'fecha_creacion']

class EspacioComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EspacioComun
        fields = ['id', 'nombre', 'descripcion', 'capacidad', 'complejo', 'activo']

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    rol = RolSerializer(read_only=True)
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source='rol',
        write_only=True
    )
    unidad_habitacional = UnidadHabitacionalSerializer(read_only=True)
    unidad_habitacional_id = serializers.PrimaryKeyRelatedField(
        queryset=UnidadHabitacional.objects.all(),
        source='unidad_habitacional',
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 
                 'rut', 'telefono', 'rol', 'rol_id', 'unidad_habitacional',
                 'unidad_habitacional_id']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

class WhiteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteList
        fields = ['id', 'email', 'estado', 'fecha_creacion', 'complejo']
        read_only_fields = ['id', 'fecha_creacion']

class PagoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='usuario',
        write_only=True
    )

    class Meta:
        model = Pago
        fields = ['id', 'usuario', 'usuario_id', 'fecha_creacion', 
                 'fecha_vencimiento', 'estado', 'monto_total']
        read_only_fields = ['id', 'fecha_creacion']

class ReservaDetalleSerializer(serializers.ModelSerializer):
    espacio = EspacioComunSerializer(read_only=True)
    espacio_id = serializers.PrimaryKeyRelatedField(
        queryset=EspacioComun.objects.all(),
        source='espacio',
        write_only=True
    )

    class Meta:
        model = ReservaDetalle
        fields = ['id', 'reserva', 'espacio', 'espacio_id', 'fecha_inicio', 
                 'fecha_fin', 'cantidad_personas']

class ReservaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='usuario',
        write_only=True
    )
    detalles = ReservaDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = Reserva
        fields = ['id', 'usuario', 'usuario_id', 'fecha_creacion', 'estado', 
                 'observaciones', 'detalles']
        read_only_fields = ['id', 'fecha_creacion']

class NotificacionSerializer(serializers.ModelSerializer):
    creador = UsuarioSerializer(read_only=True)
    creador_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='creador',
        write_only=True
    )
    destinatarios = UsuarioSerializer(many=True, read_only=True)
    destinatarios_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='destinatarios',
        write_only=True,
        many=True
    )

    class Meta:
        model = Notificacion
        fields = ['id', 'titulo', 'mensaje', 'tipo', 'fecha_creacion', 
                 'fecha_publicacion', 'creador', 'creador_id', 'destinatarios',
                 'destinatarios_ids', 'complejo']
        read_only_fields = ['id', 'fecha_creacion']

class PagoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoDetalle
        fields = '__all__'

class GastoComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoComun
        fields = '__all__'
        read_only_fields = ('creado_por', 'fecha_creacion')

    def create(self, validated_data):
        validated_data['creado_por'] = self.context['request'].user
        return super().create(validated_data)
