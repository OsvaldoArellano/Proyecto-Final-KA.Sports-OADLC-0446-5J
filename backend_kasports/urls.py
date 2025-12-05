"""
URL configuration for backend_kasports project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import never_cache

def add_cache_headers(get_response):
    """Middleware para agregar headers de no-caché a archivos estáticos"""
    def middleware(request):
        response = get_response(request)
        if request.path.startswith('/static/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
    return middleware

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_kasports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Usar str() para convertir Path a string compatible con Windows
    static_root = str(settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.STATIC_URL, document_root=static_root)
