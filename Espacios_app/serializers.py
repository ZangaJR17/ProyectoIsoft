from datetime import date, datetime, time, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import CustomUser, Cliente, Instalacion, Reserva, Administrador, Factura, Retroalimentacion 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'nombre', 'rol')
        read_only_fields = ('email', 'rol')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    rol = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'nombre', 'password', 'password2', 'rol')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Ambas contraseñas deben coincidir."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            nombre=validated_data['nombre'],
        )
        user.set_password(validated_data['password'])
        user.save()

        if user.rol == 'cliente':
            Cliente.objects.create(user=user)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        data['id'] = self.user.id
        data['email'] = self.user.email
        data['nombre'] = self.user.nombre
        data['rol'] = self.user.rol
        return data

class InstalacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instalacion
        fields = '__all__'


class ReservaSerializer(serializers.ModelSerializer):
    instalacion_nombre = serializers.CharField(source='instalacion.nombre', read_only=True)
    instalacion_precio_periodo = serializers.FloatField(source='instalacion.precio_periodo', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.nombre', read_only=True)
    
    duracion_horas = serializers.SerializerMethodField(read_only=True) # Este campo se calculará

    class Meta:
        model = Reserva
        fields = [
            'id', 'cliente', 'cliente_nombre', 'instalacion', 'instalacion_nombre',
            'instalacion_precio_periodo', 'fecha', 'horaInicio', 'horaFin',
            'estadoReserva', 'estadoPago', 'duracion_horas'
        ]
        read_only_fields = ['cliente', 'estadoReserva', 'estadoPago', 'duracion_horas']

    def get_duracion_horas(self, obj):
        if obj.horaFin and obj.horaInicio:
            dt_inicio = datetime.combine(date.today(), obj.horaInicio)
            dt_fin = datetime.combine(date.today(), obj.horaFin)

            if dt_fin < dt_inicio:
                dt_fin += timedelta(days=1)
            
            duracion = dt_fin - dt_inicio
            return duracion.total_seconds() / 3600
        return None

    def validate(self, data):
        fecha_reserva = data.get('fecha')
        hora_inicio_reserva = data.get('horaInicio')
        hora_fin_reserva = data.get('horaFin')
        instalacion_solicitada = data.get('instalacion')

        if not all([fecha_reserva, hora_inicio_reserva, hora_fin_reserva, instalacion_solicitada]):
            raise serializers.ValidationError("Todos los campos de fecha, hora de inicio, hora de fin e instalación son requeridos.")

        reserva_datetime_inicio = datetime.combine(fecha_reserva, hora_inicio_reserva)
        
        if timezone.is_aware(timezone.now()):
            reserva_datetime_inicio = timezone.make_aware(reserva_datetime_inicio, timezone.get_current_timezone())
        
        if reserva_datetime_inicio < timezone.now():
            raise serializers.ValidationError("La reserva debe ser para una fecha y hora futura.")

        if hora_inicio_reserva >= hora_fin_reserva:
            raise serializers.ValidationError("La hora de inicio no puede ser igual o posterior a la hora final.")

        reservas_existentes = Reserva.objects.filter(
            instalacion=instalacion_solicitada,
            fecha=fecha_reserva,
            estadoReserva='aceptada'
        )

        if self.instance:
            reservas_existentes = reservas_existentes.exclude(pk=self.instance.pk)

        for reserva_existente in reservas_existentes:
            if (hora_inicio_reserva < reserva_existente.horaFin and
                hora_fin_reserva > reserva_existente.horaInicio):
                raise serializers.ValidationError(
                    f"La instalación '{instalacion_solicitada.nombre}' ya tiene una reserva aprobada que se solapa en este horario "
                    f"({reserva_existente.horaInicio.strftime('%H:%M')} - {reserva_existente.horaFin.strftime('%H:%M')})."
                )
        
        dt_inicio_calc = datetime.combine(date.today(), hora_inicio_reserva)
        dt_fin_calc = datetime.combine(date.today(), hora_fin_reserva)

        if dt_fin_calc < dt_inicio_calc:
            dt_fin_calc += timedelta(days=1)
        
        duracion_horas_calculada = (dt_fin_calc - dt_inicio_calc).total_seconds() / 3600

        monto_total_calculado = instalacion_solicitada.precio_periodo * duracion_horas_calculada
        
        data['monto_total_reserva'] = monto_total_calculado

        return data

    def create(self, validated_data):
        monto_total_reserva = validated_data.pop('monto_total_reserva', None)
        reserva = super().create(validated_data)
        return reserva

    def update(self, instance, validated_data):
        validated_data.pop('monto_total_reserva', None)
        return super().update(instance, validated_data)


class FacturaSerializer(serializers.ModelSerializer):
    reserva_id = serializers.IntegerField(source='reserva.id', read_only=True)
    reserva_cliente_nombre = serializers.CharField(source='reserva.cliente.user.nombre', read_only=True)
    reserva_instalacion_nombre = serializers.CharField(source='reserva.instalacion.nombre', read_only=True)

    class Meta:
        model = Factura
        fields = '__all__' 

class RetroalimentacionSerializer(serializers.ModelSerializer):
    reserva_id = serializers.IntegerField(source='reserva.id', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.nombre', read_only=True)
    instalacion_nombre_reserva = serializers.CharField(source='reserva.instalacion.nombre', read_only=True)

    class Meta:
        model = Retroalimentacion
        fields = '__all__' 