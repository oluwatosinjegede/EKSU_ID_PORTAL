from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from idcards.views import verify_id


urlpatterns = [
    path("admin/", admin.site.urls),

    # Accounts (home/login/etc)
    path("", include("accounts.urls")),

    # ID verification
    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    # IDCards urls (download/verify extras)
    path("", include("idcards.urls")),
    

    path(
        "favicon.ico",
        RedirectView.as_view(
            url=settings.STATIC_URL + "images/favicon.ico",
            permanent=False,
        ),
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
