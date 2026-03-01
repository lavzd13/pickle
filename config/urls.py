from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve


@login_required
def protected_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.api_urls')),
    path('', include('accounts.urls')),
    re_path(r'^media/(?P<path>.*)$', protected_media),
]
