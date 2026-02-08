from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from idcards.views import verify_id


urlpatterns = [
    path("admin/", admin.site.urls),

    # -------------------------------------------------
    # ACCOUNTS (Namespaced)
    # -------------------------------------------------
    path(
        "",
        include(("accounts.urls", "accounts"), namespace="accounts"),
    ),

    # -------------------------------------------------
    # APPLICATIONS (Namespaced)
    # -------------------------------------------------

    path(
        "",
        include(("applications.urls", "applications"), namespace="applications"),
    ),


    # -------------------------------------------------
    # ID VERIFICATION (Namespaced safe)
    # -------------------------------------------------
    path(
        "verify/<uuid:uid>/",
        verify_id,
        name="verify_id",   # use idcards:verify_id in templates if needed
    ),

    # -------------------------------------------------
    # IDCARDS (Namespaced)
    # -------------------------------------------------
    path(
        "",
        include(("idcards.urls", "idcards"), namespace="idcards"),
    ),

    # -------------------------------------------------
    # FAVICON
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
# MEDIA FILES (Development)
# -------------------------------------------------
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
