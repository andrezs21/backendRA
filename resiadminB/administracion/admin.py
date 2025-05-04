from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    WhiteList, Rol, ComplejoHabitacional, UnidadHabitacional, 
    Usuario, Pago, PagoDetalle, ConfiguracionMulta, GastoComun,
    EspacioComun, Reserva, ReservaDetalle, Notificacion
)

class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('email', 'estado', 'complejo', 'fecha_creacion')
    list_filter = ('estado', 'complejo')
    search_fields = ('email',)
    date_hierarchy = 'fecha_creacion'

admin.site.register(WhiteList, WhiteListAdmin)

class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

admin.site.register(Rol, RolAdmin)

class UnidadHabitacionalInline(admin.TabularInline):
    model = UnidadHabitacional
    extra = 0

class ComplejoHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'administrador', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'direccion', 'administrador__email')
    inlines = [UnidadHabitacionalInline]

admin.site.register(ComplejoHabitacional, ComplejoHabitacionalAdmin)

class UnidadHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'complejo', 'metros_cuadrados', 'activo')
    list_filter = ('tipo', 'complejo', 'activo')
    search_fields = ('numero', 'complejo__nombre')

admin.site.register(UnidadHabitacional, UnidadHabitacionalAdmin)

class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'rut', 'telefono', 'rol', 'complejo_administrado', 'unidad_habitacional', 'is_active')
    list_filter = ('rol', 'is_active', 'complejo_administrado')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'rut', 'telefono')}),
        ('Asociaciones', {'fields': ('rol', 'complejo_administrado', 'unidad_habitacional')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'rut', 'telefono', 'rol', 'complejo_administrado', 'unidad_habitacional'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'rut')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(Usuario, UsuarioAdmin)

class PagoDetalleInline(admin.TabularInline):
    model = PagoDetalle
    extra = 0

class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_creacion', 'fecha_vencimiento', 'estado', 'monto_total')
    list_filter = ('estado', 'fecha_vencimiento')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name')
    inlines = [PagoDetalleInline]

admin.site.register(Pago, PagoAdmin)

class ConfiguracionMultaAdmin(admin.ModelAdmin):
    list_display = ('complejo', 'dias_tolerancia', 'porcentaje_multa_diaria', 'monto_minimo_multa', 'monto_maximo_multa', 'activo')
    list_filter = ('complejo', 'activo')

admin.site.register(ConfiguracionMulta, ConfiguracionMultaAdmin)

class GastoComunAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'complejo', 'monto', 'mes', 'anio', 'creado_por', 'estado')
    list_filter = ('tipo', 'complejo', 'estado', 'mes', 'anio')
    search_fields = ('descripcion', 'complejo__nombre', 'creado_por__email')

admin.site.register(GastoComun, GastoComunAdmin)

class EspacioComunAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'complejo', 'capacidad', 'activo')
    list_filter = ('complejo', 'activo')
    search_fields = ('nombre', 'complejo__nombre')

admin.site.register(EspacioComun, EspacioComunAdmin)

class ReservaDetalleInline(admin.TabularInline):
    model = ReservaDetalle
    extra = 0

class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_creacion', 'estado')
    list_filter = ('estado',)
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name')
    inlines = [ReservaDetalleInline]

admin.site.register(Reserva, ReservaAdmin)

class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'complejo', 'creador', 'fecha_publicacion')
    list_filter = ('tipo', 'complejo')
    search_fields = ('titulo', 'mensaje', 'complejo__nombre')
    filter_horizontal = ('destinatarios',)

admin.site.register(Notificacion, NotificacionAdmin)