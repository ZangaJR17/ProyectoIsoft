"""
URL configuration for Espacios_eventos project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/', include('Espacios_app.urls')), 
    
    # URLs para las plantillas HTML 
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('register.html', TemplateView.as_view(template_name='register.html'), name='register_page'),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login_page'),
    path('instalaciones.html', TemplateView.as_view(template_name='instalaciones.html'), name='instalaciones_page'),
    path('cliente.html', TemplateView.as_view(template_name='cliente.html'), name='cliente_page'),
    path('administrador.html', TemplateView.as_view(template_name='administrador.html'), name='administrador_page'), #
]
