# config/urls.py

from django.contrib import admin
from django.urls import path, include
from bodega import views as bodega_views
from django.views.generic.base import RedirectView

urlpatterns = [
    # URLs de Autenticación (AQUÍ DEBEN ESTAR)
    path('login/', bodega_views.login_view, name='login'),
    path('logout/', bodega_views.logout_view, name='logout'),
    
    # URL de la aplicación de bodega
    path('bodega/', include('bodega.urls')),
    
    # URL del Admin de Django
    path('admin/', admin.site.urls),

    # Redirección de la raíz
    path('', RedirectView.as_view(url='/bodega/', permanent=True)),
]