from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Rol, Usuario, ComplejoHabitacional, UnidadHabitacional,
    WhiteList, Pago, PagoDetalle, EspacioComun,
    Reserva, ReservaDetalle, Notificacion, ConfiguracionMulta
)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'rut', 'rol', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'rut')
    ordering = ('email',)
    list_filter = ('rol', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información Personal'), {'fields': ('first_name', 'last_name', 'rut', 'telefono')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Datos del Sistema'), {'fields': ('rol', 'unidad_habitacional')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'rut', 'telefono', 'rol'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:  # Si es un nuevo usuario
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # Si es un nuevo usuario
            form.base_fields['rol'].required = True
            form.base_fields['rut'].required = True
        return form

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(ComplejoHabitacional)
class ComplejoHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'activo', 'administrador')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    list_filter = ('activo', 'administrador')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "administrador":
            # Filtrar solo usuarios con rol de administrador
            kwargs["queryset"] = Usuario.objects.filter(rol__nombre='ADMIN')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una creación nueva
            obj.administrador = request.user
        super().save_model(request, obj, form, change)

@admin.register(UnidadHabitacional)
class UnidadHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'complejo', 'metros_cuadrados', 'activo')
    search_fields = ('numero', 'tipo')
    list_filter = ('complejo', 'activo')

@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('email', 'complejo', 'fecha_creacion', 'estado')
    search_fields = ('email', 'complejo__nombre')
    list_filter = ('estado', 'complejo')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'fecha_vencimiento', 'estado', 'monto_total')
    search_fields = ('usuario__email',)
    list_filter = ('estado', 'fecha_vencimiento')

@admin.register(ConfiguracionMulta)
class ConfiguracionMultaAdmin(admin.ModelAdmin):
    list_display = ('complejo', 'dias_tolerancia', 'porcentaje_multa_diaria', 'monto_minimo_multa', 'monto_maximo_multa', 'activo')
    search_fields = ('complejo__nombre',)
    list_filter = ('activo',)

@admin.register(PagoDetalle)
class PagoDetalleAdmin(admin.ModelAdmin):
    list_display = ('pago', 'concepto', 'monto', 'fecha_vencimiento', 'fecha_pago', 'dias_atraso', 'multa')
    search_fields = ('concepto', 'pago__usuario__email')
    list_filter = ('fecha_vencimiento', 'fecha_pago')
    readonly_fields = ('dias_atraso', 'multa')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.fecha_pago:  # Si ya tiene fecha de pago, no se puede modificar
            return ['concepto', 'monto', 'fecha_vencimiento', 'fecha_pago', 'dias_atraso', 'multa']
        return ['dias_atraso', 'multa']

@admin.register(EspacioComun)
class EspacioComunAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'complejo', 'capacidad', 'activo')
    search_fields = ('nombre',)
    list_filter = ('complejo', 'activo')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_creacion', 'estado')
    search_fields = ('usuario__email',)
    list_filter = ('estado', 'fecha_creacion')

@admin.register(ReservaDetalle)
class ReservaDetalleAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'espacio', 'fecha_inicio', 'fecha_fin')
    search_fields = ('espacio__nombre',)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'creador', 'fecha_publicacion', 'complejo')
    search_fields = ('titulo', 'mensaje')
    list_filter = ('tipo', 'fecha_publicacion', 'complejo')
