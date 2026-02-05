from django.contrib import admin
from django.urls import path, include
from idcards.views import verify_id
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    path('', include('idcards.urls')),
    path("accounts/", include("accounts.urls")),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
  

