from django.core.management.base import BaseCommand
from administracion.models import Rol

class Command(BaseCommand):
    help = 'Crea los roles iniciales del sistema'

    def handle(self, *args, **options):
        roles = [
            ('SUPERADMIN', 'Super Administrador'),
            ('ADMIN', 'Administrador de Complejo'),
            ('CONSERJE', 'Conserje'),
            ('RESIDENTE', 'Residente'),
        ]
        
        for codigo, nombre in roles:
            rol, created = Rol.objects.get_or_create(
                nombre=codigo,
                defaults={'descripcion': nombre}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Rol {nombre} creado exitosamente'))
            else:
                self.stdout.write(self.style.WARNING(f'Rol {nombre} ya existe')) 