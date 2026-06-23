import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin-django/', admin.site.urls),
    path('admin/', include('dashboard.urls')),
    path('', include('products.urls')),
    path('', include('users.urls')),
    path('cart/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG or os.environ.get('VERCEL'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
