from django.urls import path
from .views import verify_id, download_id

app_name = "idcards"   # Enables namespace (idcards:*)

urlpatterns = [
    # -------------------------------------------------
    # QR Verification (open ID in browser)
    # -------------------------------------------------
    path(
        "verify/<uuid:uid>/",
        verify_id,
        name="verify_id",
    ),

    # -------------------------------------------------
    # Force Download ID
    # -------------------------------------------------
    path(
        "verify/<uuid:uid>/download/",
        download_id,
        name="download_id",
    ),
]
