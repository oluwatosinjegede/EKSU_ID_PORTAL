from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from idcards.views import verify_id


urlpatterns = [
    # -------------------------------------------------
    # ADMIN
    # -------------------------------------------------
    path("admin/", admin.site.urls),

    # -------------------------------------------------
    # VERIFY ID (QR target — must be TOP LEVEL)
    # -------------------------------------------------
    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    # -------------------------------------------------
    # CORE APP ROUTES
    # -------------------------------------------------
    path("", include("accounts.urls")),      # login, logout, dashboard
    path("", include("applications.urls")),  # apply, approve
    path("", include("idcards.urls")),       # download, API, etc.

    # -------------------------------------------------
    # FAVICON (prevents /favicon.ico 404 spam)
    # -------------------------------------------------
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=settings.STATIC_URL + "images/favicon.ico",
            permanent=False,
        ),
    ),
]


# -------------------------------------------------
# MEDIA SERVING (Railway — no nginx)
# -------------------------------------------------
if settings.MEDIA_URL and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
