from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from idcards.views import verify_id


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Verify ID (QR target)
    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    # App routes
    path("", include("accounts.urls")),
    path("", include("idcards.urls")),

    # Optional: favicon (prevents /favicon.ico error)
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=settings.STATIC_URL + "images/favicon.ico",
            permanent=False,
        ),
    ),
]


# -------------------------------------------------
# MEDIA SERVING (Railway-safe)
# -------------------------------------------------
# Railway does not run nginx, so Django must serve media.
# This works in both DEBUG and production.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
