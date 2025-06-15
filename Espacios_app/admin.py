# Espacios_app/admin.py

from django.contrib import admin
from .models import (
    CustomUser,
    Cliente,
    Instalacion,
    Reserva,
    Administrador,
    Retroalimentacion,
    Factura,
    Reporte
)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class CustomUserAdmin(BaseUserAdmin):
   
    list_display = ('email', 'nombre', 'rol', 'is_active', 'is_staff', 'is_superuser')

    
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'rol')

    
    search_fields = ('email', 'nombre')

    
    readonly_fields = ('date_joined', 'last_login',)

    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'rol')}),
        
        ('Permisos', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('date_joined', 'last_login',)}),
    )

    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'rol', 'password', 'password2'),
        }),
    )
    ordering = ('email',)

    # Añade esto para manejar las relaciones ManyToMany (groups, user_permissions)
    filter_horizontal = ('groups', 'user_permissions',)

# Registro de todos tus modelos
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Cliente)
admin.site.register(Instalacion)
admin.site.register(Reserva)
admin.site.register(Administrador)
admin.site.register(Retroalimentacion)
admin.site.register(Factura)
admin.site.register(Reporte)
