from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# --- Manager para CustomUser (Persona) ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El campo Email debe ser establecido')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('rol', 'administrador') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# --- Modelo de Usuario Personalizado (Persona) ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    ROLES_CHOICES = (
        ('cliente', 'Cliente'),
        ('administrador', 'Administrador'),
    )

    # Atributos de Persona
    email = models.EmailField(unique=True, max_length=255) 
    nombre = models.CharField(max_length=255) 
    
    rol = models.CharField(max_length=50, choices=ROLES_CHOICES, default='cliente') 

    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre'] 

    objects = CustomUserManager() 

    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.nombre

    def get_short_name(self):
        return self.nombre

# --- Modelos para Cliente y Administrador 

class Cliente(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True) 
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.user.nombre 


class Administrador(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True) 
    
    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return self.user.nombre 

# --- Modelo Instalacion ---
class Instalacion(models.Model):
    
    ESTADO_INSTALACION_CHOICES = (
        ('disponible', 'Disponible'),
        ('en_mantenimiento', 'En Mantenimiento'),
        ('no_disponible', 'No Disponible'),
    )
    
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    capacidad = models.IntegerField()
    estado = models.CharField(max_length=50, choices=ESTADO_INSTALACION_CHOICES, default='disponible') 
    precio_periodo = models.FloatField() 
    tipo = models.CharField(max_length=100) 

    class Meta:
        verbose_name = 'Instalación'
        verbose_name_plural = 'Instalaciones'

    def __str__(self):
        return self.nombre

# --- Modelo Reserva ---
class Reserva(models.Model):
    # Definimos los estados de reserva como CHOICES
    ESTADO_RESERVA_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'), 
    )
    
    ESTADO_PAGO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('reembolsada', 'Reembolsada'), 
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas') 
    instalacion = models.ForeignKey(Instalacion, on_delete=models.CASCADE, related_name='reservas') 
    fecha = models.DateField()
    horaInicio = models.TimeField()
    horaFin = models.TimeField()
    estadoReserva = models.CharField(max_length=50, choices=ESTADO_RESERVA_CHOICES, default='pendiente') 
    estadoPago = models.CharField(max_length=50, choices=ESTADO_PAGO_CHOICES, default='pendiente') 

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva de {self.cliente.user.nombre} para {self.instalacion.nombre} el {self.fecha}"

# --- Modelo Retroalimentacion ---
class Retroalimentacion(models.Model):
    
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='retroalimentaciones') 
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='retroalimentaciones_hechas') 
    calificacion = models.IntegerField() 
    comentario = models.TextField(blank=True, null=True) 
    fecha = models.DateTimeField(auto_now_add=True) 

    class Meta:
        verbose_name = 'Retroalimentación'
        verbose_name_plural = 'Retroalimentaciones'

    def __str__(self):
        return f"Calificación {self.calificacion} para Reserva {self.reserva.id} por {self.cliente.user.nombre}"

# --- Modelo Factura ---
class Factura(models.Model):
    
    ESTADO_FACTURA_PAGO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('reembolsada', 'Reembolsada'),
    )
    
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='factura') 
    fechaPago = models.DateField(blank=True, null=True) 
    monto = models.FloatField() 
    metodoPago = models.CharField(max_length=100, blank=True, null=True) 
    estado_pago = models.CharField(max_length=50, choices=ESTADO_FACTURA_PAGO_CHOICES, default='pendiente') 

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return f"Factura #{self.id} de Reserva {self.reserva.id}"

# --- Modelo Reporte ---
class Reporte(models.Model):
    
    administrador = models.ForeignKey(Administrador, on_delete=models.CASCADE, related_name='reportes_generados') 
    fechaGeneracion = models.DateTimeField(auto_now_add=True) 
    fechaInicio = models.DateField()
    fechaFin = models.DateField()
    tipoReporte = models.CharField(max_length=100) 

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'

    def __str__(self):
        return f"Reporte {self.tipoReporte} generado por {self.administrador.user.nombre} el {self.fechaGeneracion.date()}"
