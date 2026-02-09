from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# IMPORTANT — import verify view
from idcards.views import verify_id


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================
    path("admin/", admin.site.urls),

    # =====================================================
    # ACCOUNTS
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
    # GLOBAL QR VERIFY (PRIMARY — WITH TOKEN)
    # This is what QR MUST use
    # =====================================================
    path(
        "verify/<uuid:uid>/<str:token>/",
        verify_id,
        name="verify_id",
    ),

    # =====================================================
    # OPTIONAL SHORT VERIFY (NO TOKEN ? redirects to app)
    # Keeps backward compatibility
    # =====================================================
    path(
        "verify/<uuid:uid>/",
        RedirectView.as_view(
            pattern_name="idcards:verify_id_no_token",
            permanent=False,
        ),
    ),

    # =====================================================
    # IDCARDS APP
    # Handles:
    #   /idcards/verify/<uid>/<token>/
    #   /idcards/my-id/
    #   /idcards/stream/
    # =====================================================
    path(
        "idcards/",
        include(("idcards.urls", "idcards"), namespace="idcards"),
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
# MEDIA (DEV ONLY)
# =====================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
