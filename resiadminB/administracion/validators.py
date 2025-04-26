import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validar_rut(value):
    """
    Valida que el RUT tenga el formato correcto y que el dígito verificador sea válido.
    Formato esperado: XXXXXXXX-X donde X son números y el último puede ser un número o K
    """
    # Eliminar espacios y convertir a mayúsculas
    rut = value.strip().upper()
    
    # Verificar formato básico (números + guión + dígito verificador)
    if not re.match(r'^\d{7,8}-[0-9K]$', rut):
        raise ValidationError(
            _('El RUT debe tener el formato XXXXXXXX-X (ejemplo: 12345678-9 o 12345678-K)'),
            params={'value': value},
        )
    
    # Separar número y dígito verificador
    rut_numero, dv = rut.split('-')
    
    # Calcular dígito verificador
    suma = 0
    multiplicador = 2
    
    # Calcular suma ponderada
    for r in reversed(rut_numero):
        suma += int(r) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    # Calcular dígito verificador esperado
    resto = 11 - (suma % 11)
    
    # Casos especiales
    if resto == 11:
        dv_esperado = '0'
    elif resto == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(resto)
    
    # Verificar dígito verificador
    if dv != dv_esperado:
        raise ValidationError(
            _('El dígito verificador del RUT no es válido. El dígito verificador correcto debería ser %(dv)s'),
            params={'value': value, 'dv': dv_esperado},
        )
    
    # Formatear RUT antes de guardar (agregar puntos)
    rut_formateado = ''
    for i, digito in enumerate(reversed(rut_numero)):
        if i > 0 and i % 3 == 0:
            rut_formateado = '.' + rut_formateado
        rut_formateado = digito + rut_formateado
    
    return f"{rut_formateado}-{dv}" 