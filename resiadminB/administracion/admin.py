from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Rol, Usuario, ComplejoHabitacional, UnidadHabitacional,
    WhiteList, Pago, PagoDetalle, EspacioComun,
    Reserva, ReservaDetalle, Notificacion, ConfiguracionMulta,
    GastoComun
)

# Definir inlines para mostrar relaciones anidadas
class UnidadHabitacionalInline(admin.TabularInline):
    model = UnidadHabitacional
    extra = 0
    fields = ('numero', 'tipo', 'metros_cuadrados', 'activo')

class PagoDetalleInline(admin.TabularInline):
    model = PagoDetalle
    extra = 0
    fields = ('concepto', 'monto', 'fecha_vencimiento', 'fecha_pago', 'dias_atraso', 'multa')
    readonly_fields = ('dias_atraso', 'multa')

class ReservaDetalleInline(admin.TabularInline):
    model = ReservaDetalle
    extra = 0
    fields = ('espacio', 'fecha_inicio', 'fecha_fin', 'cantidad_personas')

class ConfiguracionMultaInline(admin.TabularInline):
    model = ConfiguracionMulta
    extra = 0
    fields = ('dias_tolerancia', 'porcentaje_multa_diaria', 'monto_minimo_multa', 'monto_maximo_multa', 'activo')

class ResidenteInline(admin.TabularInline):
    model = Usuario
    extra = 0
    fields = ('email', 'first_name', 'last_name', 'rut', 'is_active')
    verbose_name = "Residente"
    verbose_name_plural = "Residentes"
    readonly_fields = ('email', 'first_name', 'last_name', 'rut')
    can_delete = False

    def get_queryset(self, request):
        # Filtrar solo usuarios con rol de residente
        qs = super().get_queryset(request)
        return qs.filter(rol__nombre='RESIDENTE')

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'rut', 'rol', 'unidad_habitacional', 'complejo_display', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'rut', 'unidad_habitacional__complejo__nombre')
    ordering = ('email',)
    list_filter = ('rol', 'is_active', 'unidad_habitacional__complejo')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Información Personal'), {'fields': ('first_name', 'last_name', 'rut', 'telefono')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Datos del Sistema'), {'fields': ('rol', 'unidad_habitacional', 'complejo_info')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'rut', 'telefono', 'rol', 'unidad_habitacional'),
        }),
    )
    
    readonly_fields = ('complejo_info',)

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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "unidad_habitacional":
            # Mostrar unidad_habitacional con formato más descriptivo
            kwargs["queryset"] = UnidadHabitacional.objects.select_related('complejo')
        elif db_field.name == "rol":
            # Mostrar roles en orden lógico
            kwargs["queryset"] = Rol.objects.all().order_by('nombre')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def complejo_display(self, obj):
        """Mostrar el complejo asociado al usuario a través de su unidad"""
        if obj.unidad_habitacional and obj.unidad_habitacional.complejo:
            return obj.unidad_habitacional.complejo.nombre
        return "-"
    complejo_display.short_description = "Complejo"
    complejo_display.admin_order_field = 'unidad_habitacional__complejo__nombre'
    
    def complejo_info(self, obj):
        """Mostrar información detallada del complejo en el formulario"""
        if obj.unidad_habitacional and obj.unidad_habitacional.complejo:
            complejo = obj.unidad_habitacional.complejo
            return format_html(
                '<div style="padding: 10px; background-color: #f8f9fa; border-radius: 4px;">'
                '<h3 style="margin-top: 0;">Información del Complejo</h3>'
                '<p><strong>Nombre:</strong> {0}</p>'
                '<p><strong>Dirección:</strong> {1}</p>'
                '<p><strong>Teléfono:</strong> {2}</p>'
                '<p><strong>Email:</strong> {3}</p>'
                '<p><strong>Administrador:</strong> {4}</p>'
                '</div>',
                complejo.nombre,
                complejo.direccion,
                complejo.telefono or "-",
                complejo.email or "-",
                complejo.administrador.get_full_name() if complejo.administrador else "-"
            )
        return "No está asociado a ningún complejo."
    complejo_info.short_description = "Información del Complejo"

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'usuarios_count')
    search_fields = ('nombre',)
    
    def usuarios_count(self, obj):
        return obj.usuarios.count()
    usuarios_count.short_description = 'Número de usuarios'

@admin.register(ComplejoHabitacional)
class ComplejoHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'unidades_count', 'residentes_count', 'activo', 'administrador')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    list_filter = ('activo',)
    inlines = [UnidadHabitacionalInline, ConfiguracionMultaInline]
    
    def unidades_count(self, obj):
        return obj.unidades.count()
    unidades_count.short_description = 'Unidades'
    
    def residentes_count(self, obj):
        """Contar residentes en todas las unidades del complejo"""
        count = Usuario.objects.filter(
            unidad_habitacional__complejo=obj,
            rol__nombre='RESIDENTE'
        ).count()
        return count
    residentes_count.short_description = 'Residentes'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "administrador":
            # Filtrar solo usuarios con rol de administrador
            kwargs["queryset"] = Usuario.objects.filter(rol__nombre='ADMIN')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(UnidadHabitacional)
class UnidadHabitacionalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'complejo', 'metros_cuadrados', 'residentes_count', 'activo')
    search_fields = ('numero', 'tipo', 'complejo__nombre')
    list_filter = ('complejo', 'activo', 'tipo')
    inlines = [ResidenteInline]
    
    def residentes_count(self, obj):
        return obj.residentes.count()
    residentes_count.short_description = 'Residentes'

@admin.register(WhiteList)
class WhiteListAdmin(admin.ModelAdmin):
    list_display = ('email', 'complejo', 'fecha_creacion', 'estado')
    search_fields = ('email', 'complejo__nombre')
    list_filter = ('estado', 'complejo')
    date_hierarchy = 'fecha_creacion'

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'complejo_display', 'fecha_creacion', 'fecha_vencimiento', 'estado', 'monto_total', 'items_count')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name', 'usuario__rut')
    list_filter = ('estado', 'fecha_vencimiento', 'usuario__unidad_habitacional__complejo')
    date_hierarchy = 'fecha_creacion'
    inlines = [PagoDetalleInline]
    
    def items_count(self, obj):
        return obj.detalles.count()
    items_count.short_description = 'Items'
    
    def complejo_display(self, obj):
        """Mostrar el complejo asociado al pago a través del usuario"""
        if obj.usuario and obj.usuario.unidad_habitacional and obj.usuario.unidad_habitacional.complejo:
            return obj.usuario.unidad_habitacional.complejo.nombre
        return "-"
    complejo_display.short_description = "Complejo"
    complejo_display.admin_order_field = 'usuario__unidad_habitacional__complejo__nombre'

@admin.register(ConfiguracionMulta)
class ConfiguracionMultaAdmin(admin.ModelAdmin):
    list_display = ('complejo', 'dias_tolerancia', 'porcentaje_multa_diaria', 'monto_minimo_multa', 'monto_maximo_multa', 'activo')
    search_fields = ('complejo__nombre',)
    list_filter = ('activo', 'complejo')

@admin.register(PagoDetalle)
class PagoDetalleAdmin(admin.ModelAdmin):
    list_display = ('pago', 'usuario_display', 'complejo_display', 'concepto', 'monto', 'fecha_vencimiento', 'fecha_pago', 'dias_atraso', 'multa')
    search_fields = ('concepto', 'pago__usuario__email', 'pago__usuario__rut')
    list_filter = ('fecha_vencimiento', 'fecha_pago', 'pago__usuario__unidad_habitacional__complejo')
    readonly_fields = ('dias_atraso', 'multa')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.fecha_pago:  # Si ya tiene fecha de pago, no se puede modificar
            return ['concepto', 'monto', 'fecha_vencimiento', 'fecha_pago', 'dias_atraso', 'multa']
        return ['dias_atraso', 'multa']
    
    def usuario_display(self, obj):
        """Mostrar el usuario asociado al pago detalle"""
        if obj.pago and obj.pago.usuario:
            return obj.pago.usuario.email
        return "-"
    usuario_display.short_description = "Usuario"
    
    def complejo_display(self, obj):
        """Mostrar el complejo asociado al pago detalle"""
        if obj.pago and obj.pago.usuario and obj.pago.usuario.unidad_habitacional and obj.pago.usuario.unidad_habitacional.complejo:
            return obj.pago.usuario.unidad_habitacional.complejo.nombre
        return "-"
    complejo_display.short_description = "Complejo"

@admin.register(EspacioComun)
class EspacioComunAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'complejo', 'capacidad', 'reservas_count', 'activo')
    search_fields = ('nombre', 'complejo__nombre')
    list_filter = ('complejo', 'activo')
    
    def reservas_count(self, obj):
        return obj.reservas.count()
    reservas_count.short_description = 'Reservas'

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'complejo_display', 'fecha_creacion', 'estado', 'espacios_count')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name', 'usuario__rut')
    list_filter = ('estado', 'fecha_creacion', 'usuario__unidad_habitacional__complejo')
    date_hierarchy = 'fecha_creacion'
    inlines = [ReservaDetalleInline]
    
    def espacios_count(self, obj):
        return obj.detalles.count()
    espacios_count.short_description = 'Espacios'
    
    def complejo_display(self, obj):
        """Mostrar el complejo asociado a la reserva a través del usuario"""
        if obj.usuario and obj.usuario.unidad_habitacional and obj.usuario.unidad_habitacional.complejo:
            return obj.usuario.unidad_habitacional.complejo.nombre
        return "-"
    complejo_display.short_description = "Complejo"
    complejo_display.admin_order_field = 'usuario__unidad_habitacional__complejo__nombre'

@admin.register(ReservaDetalle)
class ReservaDetalleAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'usuario_display', 'complejo_display', 'espacio', 'fecha_inicio', 'fecha_fin', 'cantidad_personas')
    search_fields = ('espacio__nombre', 'reserva__usuario__email')
    list_filter = ('fecha_inicio', 'espacio', 'espacio__complejo')
    
    def usuario_display(self, obj):
        """Mostrar el usuario asociado al detalle de reserva"""
        if obj.reserva and obj.reserva.usuario:
            return obj.reserva.usuario.email
        return "-"
    usuario_display.short_description = "Usuario"
    
    def complejo_display(self, obj):
        """Mostrar el complejo asociado al detalle de reserva"""
        if obj.espacio and obj.espacio.complejo:
            return obj.espacio.complejo.nombre
        return "-"
    complejo_display.short_description = "Complejo"

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'creador', 'fecha_publicacion', 'complejo', 'destinatarios_count')
    search_fields = ('titulo', 'mensaje', 'creador__email', 'complejo__nombre')
    list_filter = ('tipo', 'fecha_publicacion', 'complejo')
    date_hierarchy = 'fecha_publicacion'
    filter_horizontal = ('destinatarios',)
    
    def destinatarios_count(self, obj):
        return obj.destinatarios.count()
    destinatarios_count.short_description = 'Destinatarios'

@admin.register(GastoComun)
class GastoComunAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descripcion', 'monto', 'complejo', 'mes', 'anio', 'fecha', 'estado', 'creado_por')
    search_fields = ('descripcion', 'complejo__nombre')
    list_filter = ('tipo', 'estado', 'complejo', 'mes', 'anio')
    date_hierarchy = 'fecha'