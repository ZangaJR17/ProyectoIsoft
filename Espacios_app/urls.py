from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView 
from . import views 

# Importa las clases de vistas directamente para usar .as_view() o en el router
from .views import (
    CustomUserViewSet, ReservaViewSet, RegisterView, CustomTokenObtainPairView, 
    InstalacionListView, AdminDashboardView, InstalacionAdminViewSet, ReportesView,
    
)


router = DefaultRouter()
router.register(r'users', CustomUserViewSet) 
router.register(r'reservas', ReservaViewSet) 
router.register(r'admin/instalaciones', InstalacionAdminViewSet) #


urlpatterns = [
    # URLs para páginas HTML (frontend)
    path('register.html', views.register_view, name='register_view'), 
    path('login.html', views.login_view, name='login_view'),
    path('cliente.html', views.cliente_panel, name='cliente_panel'),
    path('administrador.html', views.administrador_panel, name='administrador_panel'), #
    path('', views.index_view, name='index_view'), 

    # APIs de Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'), 
    
    # API para listar instalaciones (para clientes)
    path('instalaciones/', InstalacionListView.as_view(), name='instalacion_list'), 

    # APIs de la aplicación (usando el router de DRF para ModelViewSets)
    path('', include(router.urls)), 

    # Endpoint para las reservas del cliente logueado (misma vista, diferente queryset)
    path('mis_reservas/', ReservaViewSet.as_view({'get': 'list'}), name='mis_reservas_list'),

    # Endpoint para obtener el perfil del usuario logueado
    path('me/', CustomUserViewSet.as_view({'get': 'retrieve_current_user'}), name='current_user_profile'),

    # --- NUEVAS APIs para el Panel de Administrador ---
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/reports/', ReportesView.as_view(), name='admin_reports'),
]