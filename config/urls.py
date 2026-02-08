from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================
    path("admin/", admin.site.urls),

    # =====================================================
    # ACCOUNTS (ROOT)
    # =====================================================
    path(
        "",
        include(("accounts.urls", "accounts"), namespace="accounts"),
    ),

    # =====================================================
    # APPLICATIONS
    # =====================================================
    path(
        "",
        include(("applications.urls", "applications"), namespace="applications"),
    ),

    # =====================================================
    # IDCARDS (FAILOVER READY)
    # Handles:
    #   /idcards/verify/<uid>/
    #   /idcards/verify/<uid>/download/
    #   /idcards/my-id/
    # =====================================================
    path(
        "idcards/",
        include(("idcards.urls", "idcards"), namespace="idcards"),
    ),

    # =====================================================
    # GLOBAL VERIFY SHORT URL (QR CODE SAFE)
    # Allows QR to work without /idcards/ prefix
    # =====================================================
    path(
        "verify/<uuid:uid>/",
        RedirectView.as_view(
            pattern_name="idcards:verify_id",
            permanent=False,
        ),
    ),

    # =====================================================
    # FAVICON
    # =====================================================
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=settings.STATIC_URL + "images/favicon.ico",
            permanent=False,
        ),
    ),
]


# =====================================================
# MEDIA FILES (DEV ONLY — ignored in production)
# =====================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
