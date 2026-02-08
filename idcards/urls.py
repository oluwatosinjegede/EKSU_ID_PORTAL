from django.urls import path
from .views import verify_id, download_id, view_id_card

app_name = "idcards"


urlpatterns = [

    # =====================================================
    # PUBLIC — QR CODE VERIFICATION
    # Opens ID in browser (Cloudinary OR failover stream)
    # =====================================================
    path(
        "verify/<uuid:uid>/",
        verify_id,
        name="verify_id",
    ),

    # =====================================================
    # PUBLIC — FORCE DOWNLOAD
    # Forces download (Cloudinary OR failover stream)
    # =====================================================
    path(
        "verify/<uuid:uid>/download/",
        download_id,
        name="download_id",
    ),

    # =====================================================
    # PRIVATE — STUDENT VIEW OWN ID
    # Inline display with failover
    # =====================================================
    path(
        "my-id/",
        view_id_card,
        name="view_my_id",
    ),
]
