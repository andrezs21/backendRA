from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from decimal import Decimal
from datetime import datetime, timedelta
from .validators import validar_rut
from django.core.exceptions import ValidationError

# Create your models here.

class WhiteList(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente de registro'),
        ('REGISTRADO', 'Cuenta creada'),
    )
    
    email = models.EmailField(unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    complejo = models.ForeignKey('ComplejoHabitacional', on_delete=models.CASCADE, related_name='whitelist', null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.get_estado_display()}" + (f" - {self.complejo.nombre}" if self.complejo else "")

    class Meta:
        verbose_name = "Email Autorizado"
        verbose_name_plural = "Emails Autorizados"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        
        # Validar campos requeridos solo para usuarios normales
        if not extra_fields.get('is_superuser'):
            required_fields = ['first_name', 'last_name', 'rut']
            for field in required_fields:
                if field not in extra_fields:
                    raise ValueError(f'El campo {field} es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Establecer valores por defecto para superusuarios
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'Super')
        extra_fields.setdefault('rut', '00.000.000-0')
        
        # No validar campos requeridos para superusuarios
        return self.create_user(email, password, **extra_fields)

class Rol(models.Model):
    ROLES = (
        ('SUPERADMIN', 'Super Administrador'),
        ('ADMIN', 'Administrador de Complejo'),
        ('CONSERJE', 'Conserje'),
        ('RESIDENTE', 'Residente'),
    )
    
    nombre = models.CharField(max_length=50, choices=ROLES, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.get_nombre_display()

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

class ComplejoHabitacional(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    administrador = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='complejos_administrados')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Complejo Habitacional"
        verbose_name_plural = "Complejos Habitacionales"

class UnidadHabitacional(models.Model):
    numero = models.CharField(max_length=10)
    tipo = models.CharField(max_length=50)  # Departamento, Casa, etc.
    complejo = models.ForeignKey(ComplejoHabitacional, on_delete=models.CASCADE, related_name='unidades')
    metros_cuadrados = models.DecimalField(max_digits=6, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.complejo.nombre} - {self.tipo} {self.numero}"

    class Meta:
        verbose_name = "Unidad Habitacional"
        verbose_name_plural = "Unidades Habitacionales"
        unique_together = ['numero', 'complejo']

class Usuario(AbstractUser):
    rut = models.CharField(
        max_length=13,
        unique=True,
        validators=[validar_rut],
        help_text="Formato: 12.345.678-9 o 12.345.678-K"
    )
    telefono = models.CharField(max_length=15, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios', null=True)
    unidad_habitacional = models.ForeignKey('UnidadHabitacional', on_delete=models.SET_NULL, null=True, blank=True, related_name='residentes')
    complejo_administrado = models.ForeignKey(ComplejoHabitacional, on_delete=models.SET_NULL, null=True, blank=True, related_name='administradores')

    # Sobreescribimos el campo email para hacerlo único
    email = models.EmailField(unique=True)
    
    # No necesitamos username, usaremos email para login
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'rut']

    objects = CustomUserManager()

    def clean(self):
        super().clean()
        # Si el usuario es residente, debe tener una unidad habitacional asignada
        if self.rol and self.rol.nombre == 'RESIDENTE' and not self.unidad_habitacional:
            raise ValidationError('Los residentes deben tener una unidad habitacional asignada')
        
        # Si el usuario es administrador, debe tener un complejo asignado
        if self.rol and self.rol.nombre == 'ADMIN' and not self.complejo_administrado:
            raise ValidationError('Los administradores deben tener un complejo habitacional asignado')

    def save(self, *args, **kwargs):
        # Si el usuario es administrador y se asigna un complejo, actualizar también la relación inversa
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if self.rol and self.rol.nombre == 'ADMIN' and self.complejo_administrado:
            # Actualizar el campo administrador del complejo
            if self.complejo_administrado.administrador != self:
                self.complejo_administrado.administrador = self
                self.complejo_administrado.save(update_fields=['administrador'])

    def __str__(self):
        base_str = f"{self.get_full_name()} ({self.email})"
        if self.rol and self.rol.nombre == 'ADMIN' and self.complejo_administrado:
            return f"{base_str} - Admin de {self.complejo_administrado.nombre}"
        return base_str

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Pago(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('CANCELADO', 'Cancelado'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pagos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Pago {self.id} - {self.usuario.email}"

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

class ConfiguracionMulta(models.Model):
    complejo = models.ForeignKey(ComplejoHabitacional, on_delete=models.CASCADE, related_name='configuraciones_multas')
    dias_tolerancia = models.IntegerField(default=0, help_text="Días de gracia antes de aplicar multa")
    porcentaje_multa_diaria = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de multa por día de atraso")
    monto_minimo_multa = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto mínimo de multa")
    monto_maximo_multa = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto máximo de multa")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Configuración de multas - {self.complejo.nombre}"

    class Meta:
        verbose_name = "Configuración de Multa"
        verbose_name_plural = "Configuraciones de Multas"

class PagoDetalle(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='detalles')
    concepto = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    dias_atraso = models.IntegerField(default=0)
    fecha_pago = models.DateField(null=True, blank=True)

    def calcular_multa(self):
        if not self.fecha_pago:
            return Decimal('0.00')
        
        configuracion = ConfiguracionMulta.objects.filter(
            complejo=self.pago.usuario.unidad_habitacional.complejo,
            activo=True
        ).first()
        
        if not configuracion:
            return Decimal('0.00')
        
        dias_atraso = (self.fecha_pago - self.fecha_vencimiento).days - configuracion.dias_tolerancia
        if dias_atraso <= 0:
            return Decimal('0.00')
        
        self.dias_atraso = dias_atraso
        
        # Calcular multa base
        multa_base = (self.monto * configuracion.porcentaje_multa_diaria / 100) * dias_atraso
        
        # Aplicar límites
        if multa_base < configuracion.monto_minimo_multa:
            multa_base = configuracion.monto_minimo_multa
        elif multa_base > configuracion.monto_maximo_multa:
            multa_base = configuracion.monto_maximo_multa
        
        return multa_base

    def save(self, *args, **kwargs):
        if self.fecha_pago:
            self.multa = self.calcular_multa()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.concepto} - ${self.monto}"

    class Meta:
        verbose_name = "Detalle de Pago"
        verbose_name_plural = "Detalles de Pago"

class GastoComun(models.Model):
    TIPOS = (
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('LIMPIEZA', 'Limpieza'),
        ('SEGURIDAD', 'Seguridad'),
        ('ADMINISTRACION', 'Administración'),
        ('OTROS', 'Otros'),
    )
    
    complejo = models.ForeignKey(ComplejoHabitacional, on_delete=models.CASCADE, related_name='gastos_comunes')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    mes = models.IntegerField()  # 1-12
    anio = models.IntegerField()
    creado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='gastos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[('PENDIENTE', 'Pendiente'), ('APROBADO', 'Aprobado'), ('RECHAZADO', 'Rechazado')], default='PENDIENTE')

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.complejo.nombre} - {self.mes}/{self.anio}"

    class Meta:
        verbose_name = "Gasto Común"
        verbose_name_plural = "Gastos Comunes"
        ordering = ['-fecha', '-fecha_creacion']

class EspacioComun(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    capacidad = models.IntegerField()
    complejo = models.ForeignKey(ComplejoHabitacional, on_delete=models.CASCADE, related_name='espacios_comunes')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.complejo.nombre}"

    class Meta:
        verbose_name = "Espacio Común"
        verbose_name_plural = "Espacios Comunes"

class Reserva(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Reserva {self.id} - {self.usuario.email}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

class ReservaDetalle(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='detalles')
    espacio = models.ForeignKey(EspacioComun, on_delete=models.CASCADE, related_name='reservas')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    cantidad_personas = models.IntegerField()

    def __str__(self):
        return f"{self.espacio.nombre} - {self.fecha_inicio}"

    class Meta:
        verbose_name = "Detalle de Reserva"
        verbose_name_plural = "Detalles de Reserva"

class Notificacion(models.Model):
    TIPOS = (
        ('INFO', 'Informativa'),
        ('ALERTA', 'Alerta'),
        ('URGENTE', 'Urgente'),
    )
    
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INFO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_publicacion = models.DateTimeField()
    creador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_creadas')
    destinatarios = models.ManyToManyField(Usuario, related_name='notificaciones_recibidas')
    complejo = models.ForeignKey(ComplejoHabitacional, on_delete=models.CASCADE, related_name='notificaciones')

    def __str__(self):
        return f"{self.titulo} - {self.complejo.nombre}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_publicacion']