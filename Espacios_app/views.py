from django.shortcuts import render
from rest_framework import generics, status, permissions, viewsets 
from rest_framework.response import Response
from rest_framework.views import APIView 
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication 
from django.db.models import Count, Sum 
from django.db.models.functions import TruncMonth 
from django.shortcuts import get_object_or_404 

from .models import CustomUser, Instalacion, Reserva, Cliente, Administrador, Factura, Retroalimentacion 
from .serializers import (
    RegisterSerializer, CustomTokenObtainPairSerializer, InstalacionSerializer, 
    ReservaSerializer, CustomUserSerializer, FacturaSerializer, RetroalimentacionSerializer 
)


import datetime
from datetime import date, time, timedelta
from django.utils import timezone 

# --- Vista para el Registro de Usuarios ---
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny] 
    authentication_classes = [] 

    def post(self, request, *args, **kwargs):
        print("\n--- RegisterView.post() HA SIDO ALCANZADO ---") 
        print(f"Datos recibidos para registro: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer) 

        headers = self.get_success_headers(serializer.data)
        return Response({
            "message": "Usuario registrado exitosamente.",
            "user_id": serializer.instance.id,
            "email": serializer.instance.email,
            "rol": serializer.instance.rol
        }, status=status.HTTP_201_CREATED, headers=headers)


# --- Vista Personalizada para la Obtención de Tokens (Login) ---
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        print("\n--- CustomTokenObtainPairView.post() HA SIDO ALCANZADO ---") 
        print(f"Datos recibidos para login: {request.data}")
        
        response = super().post(request, *args, **kwargs) 
        
        if response.status_code == 200:
            print(f"Login exitoso para {request.data.get('email')}")
        else:
            print(f"Fallo en el login para {request.data.get('email')}")

        return response

# --- Ejemplo de Vista Protegida---
class ProtectedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        print("\n--- ProtectedView.get() HA SIDO ALCANZADO ---")
        return Response({"message": f"¡Bienvenido, {request.user.nombre}! Has accedido a una ruta protegida con tu rol de {request.user.rol}."})
    
# --- Vista para listar instalaciones (ListAPIView para clientes) ---
class InstalacionListView(generics.ListAPIView): 
    queryset = Instalacion.objects.filter(estado='disponible') 
    serializer_class = InstalacionSerializer
    permission_classes = [permissions.AllowAny] 
    authentication_classes = [] 

    def get_queryset(self):
        queryset = super().get_queryset()
        limit = self.request.query_params.get('limit', None)
        if limit:
            try:
                limit = int(limit)
                return queryset[:limit]
            except ValueError:
                pass 
        return queryset 


# --- Vistas para renderizar plantillas HTML ---
def index_view(request):
    return render(request, 'Espacios_app/index.html')

def register_view(request):
    return render(request, 'Espacios_app/register.html') 

def login_view(request): 
    return render(request, 'Espacios_app/login.html')

def cliente_panel(request):
    return render(request, 'Espacios_app/cliente.html')

def administrador_panel(request): 
    return render(request, 'Espacios_app/administrador.html')


# --- CustomUserViewSet para manejar usuarios ---
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def retrieve_current_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

# --- ViewSet para Reservas ---
class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            estado_reserva = self.request.query_params.get('estadoReserva', None)
            estado_pago = self.request.query_params.get('estadoPago', None)
            queryset = Reserva.objects.all()
            if estado_reserva:
                queryset = queryset.filter(estadoReserva=estado_reserva)
            if estado_pago:
                queryset = queryset.filter(estadoPago=estado_pago)
            return queryset.order_by('-fecha', '-horaInicio')
        
        queryset = Reserva.objects.filter(cliente__user=self.request.user)
        estado_reserva = self.request.query_params.get('estadoReserva', None)
        estado_pago = self.request.query_params.get('estadoPago', None)
        if estado_reserva:
            queryset = queryset.filter(estadoReserva=estado_reserva)
        if estado_pago:
            queryset = queryset.filter(estadoPago=estado_pago)
        return queryset.order_by('-fecha', '-horaInicio')

    def perform_create(self, serializer):
        if self.request.user.rol == 'cliente':
            cliente_instance = Cliente.objects.get(user=self.request.user)
            serializer.save(
                cliente=cliente_instance, 
                estadoReserva='pendiente', 
                estadoPago='pendiente'     
            )
        else:
            serializer.save(
                estadoReserva='pendiente', 
                estadoPago='pendiente'     
            )
            

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pagar(self, request, pk=None):
        reserva = get_object_or_404(Reserva, pk=pk)
        
        if not (request.user.is_staff or (request.user.rol == 'cliente' and reserva.cliente.user == request.user)):
            return Response({'detail': 'No tienes permiso para realizar esta acción.'}, status=status.HTTP_403_FORBIDDEN)

        if reserva.estadoReserva != 'aceptada': 
            return Response({'detail': 'Solo se pueden pagar reservas con estado "aceptada".'}, status=status.HTTP_400_BAD_REQUEST)

        if reserva.estadoPago == 'pagada': 
            return Response({'detail': 'Esta reserva ya ha sido pagada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        monto_calculado = reserva.instalacion.precio_periodo * ReservaSerializer().get_duracion_horas(reserva) 

        from .models import Factura 

        Factura.objects.create(
            reserva=reserva,
            fechaPago=timezone.now().date(), 
            monto=monto_calculado,
            metodoPago=request.data.get('metodoPago', 'Sin especificar'), 
            estado_pago='pagada' 
        )

        reserva.estadoPago = 'pagada' 
        reserva.save()
        serializer = self.get_serializer(reserva)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser]) 
    def aprobar(self, request, pk=None):
        reserva = get_object_or_404(Reserva, pk=pk)
        
        if reserva.estadoReserva != 'pendiente': 
            return Response({'detail': 'Solo se pueden aprobar reservas con estado "pendiente".'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import Factura 

        try:
            dt_inicio_calc = datetime.datetime.combine(reserva.fecha, reserva.horaInicio)
            dt_fin_calc = datetime.datetime.combine(reserva.fecha, reserva.horaFin)
            if dt_fin_calc < dt_inicio_calc:
                dt_fin_calc += timedelta(days=1)
            duracion_horas = (dt_fin_calc - dt_inicio_calc).total_seconds() / 3600
            monto_calculado = reserva.instalacion.precio_periodo * duracion_horas

            factura = Factura.objects.create(
                reserva=reserva,
                fechaPago=None, 
                monto=monto_calculado,
                metodoPago=None,
                estado_pago='pendiente' 
            )

            reserva.estadoReserva = 'aceptada' 
            reserva.save()
            
            serializer = self.get_serializer(reserva)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': f'Error al aprobar la reserva o crear la factura: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser]) 
    def rechazar(self, request, pk=None):
        reserva = get_object_or_404(Reserva, pk=pk)

        if reserva.estadoReserva != 'pendiente': 
            return Response({'detail': 'Solo se pueden rechazar reservas con estado "pendiente".'}, status=status.HTTP_400_BAD_REQUEST)
        
        reserva.estadoReserva = 'rechazada' 
        reserva.save()
        serializer = self.get_serializer(reserva)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancelar(self, request, pk=None):
        reserva = get_object_or_404(Reserva, pk=pk)

        if not (request.user.is_staff or (request.user.rol == 'cliente' and reserva.cliente.user == request.user)):
            return Response({'detail': 'No tienes permiso para cancelar esta reserva.'}, status=status.HTTP_403_FORBIDDEN)

        if reserva.estadoReserva in ['rechazada', 'cancelada']: 
            return Response({'detail': f'Esta reserva ya se encuentra en estado "{reserva.estadoReserva}". No se puede cancelar.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if reserva.estadoPago == 'pagada': 
            return Response({'detail': 'Esta reserva ya ha sido pagada. No se puede cancelar directamente, requiere un reembolso.'}, status=status.HTTP_400_BAD_REQUEST)

        reserva.estadoReserva = 'cancelada' 
        reserva.save()
        serializer = self.get_serializer(reserva)
        return Response(serializer.data, status=status.HTTP_200_OK)




# Dashboard del Administrador
class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ReservaSerializer 

    def get(self, request, *args, **kwargs):
        total_users = CustomUser.objects.count()
        total_clients = Cliente.objects.count()
        total_administrators = Administrador.objects.count()
        total_facilities = Instalacion.objects.count()
        
        pending_reservations_count = Reserva.objects.filter(estadoReserva='pendiente').count()
        accepted_reservations_count = Reserva.objects.filter(estadoReserva='aceptada').count()
        
        total_invoices_amount = Factura.objects.filter(estado_pago='pagada').aggregate(total=Sum('monto'))['total'] or 0.0

        latest_pending_reservations = Reserva.objects.filter(estadoReserva='pendiente').order_by('-fecha', '-horaInicio')[:5]
        latest_pending_reservations_serializer = ReservaSerializer(latest_pending_reservations, many=True)

        return Response({
            'total_users': total_users,
            'total_clients': total_clients,
            'total_administrators': total_administrators,
            'total_facilities': total_facilities,
            'pending_reservations_count': pending_reservations_count,
            'accepted_reservations_count': accepted_reservations_count,
            'total_invoices_amount': total_invoices_amount,
            'latest_pending_reservations': latest_pending_reservations_serializer.data,
        }, status=status.HTTP_200_OK)

# Gestión CRUD de Instalaciones para Administradores
class InstalacionAdminViewSet(viewsets.ModelViewSet):
    queryset = Instalacion.objects.all()
    serializer_class = InstalacionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] 

# Reportes para Administradores
class ReportesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, *args, **kwargs):
        report_type = request.query_params.get('type')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        start_date = None
        end_date = None
        if start_date_str:
            try:
                
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Formato de fecha de inicio inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if end_date_str:
            try:
               
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Formato de fecha de fin inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        data = []
        if report_type == 'reservas':
            queryset = Reserva.objects.all()
            if start_date:
                queryset = queryset.filter(fecha__gte=start_date)
            if end_date:
                queryset = queryset.filter(fecha__lte=end_date)
            
            estado_reserva_filter = request.query_params.get('estado')
            if estado_reserva_filter:
                queryset = queryset.filter(estadoReserva=estado_reserva_filter.lower())
            
            data = ReservaSerializer(queryset.order_by('-fecha', '-horaInicio'), many=True).data

        elif report_type == 'clientes':
            queryset = CustomUser.objects.filter(rol='cliente') 
            if start_date:
                queryset = queryset.filter(date_joined__date__gte=start_date) 
            if end_date:
                queryset = queryset.filter(date_joined__date__lte=end_date)
            data = CustomUserSerializer(queryset.order_by('-date_joined'), many=True).data

        elif report_type == 'facturas':
            queryset = Factura.objects.all()
            if start_date:
                queryset = queryset.filter(fechaPago__gte=start_date) 
            if end_date:
                queryset = queryset.filter(fechaPago__lte=end_date)
            
            estado_pago_filter = request.query_params.get('estado')
            if estado_pago_filter:
                queryset = queryset.filter(estado_pago=estado_pago_filter.lower())

            data = FacturaSerializer(queryset.order_by('-fechaPago'), many=True).data
        
        elif report_type == 'retroalimentacion':
            queryset = Retroalimentacion.objects.all()
            if start_date:
                queryset = queryset.filter(fecha__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(fecha__date__lte=end_date)
            
            data = RetroalimentacionSerializer(queryset.order_by('-fecha'), many=True).data

        else:
            return Response({"error": "Tipo de reporte inválido. Opciones válidas: reservas, clientes, facturas, retroalimentacion."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)