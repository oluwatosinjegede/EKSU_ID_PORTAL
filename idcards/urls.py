from django.urls import path

from .views import (
    verify_id,
    download_id,
    view_id_card,
    download_id_stream,
)

app_name = "idcards"


urlpatterns = [

    # =====================================================
    # PUBLIC — QR CODE VERIFICATION
    # Opens ID in browser (Cloudinary OR Failover)
    # =====================================================
    path(
        "verify/<uuid:uid>/",
        verify_id,
        name="verify_id",
    ),

    # =====================================================
    # PUBLIC — FORCE DOWNLOAD
    # =====================================================
    path(
        "verify/<uuid:uid>/download/",
        download_id,
        name="download_id",
    ),

    # =====================================================
    # PRIVATE — STUDENT VIEW OWN ID
    # Uses logged-in student (no UID required)
    # =====================================================
    path(
        "my-id/",
        view_id_card,   # view must support logged-in user mode
        name="view_my_id",
    ),

    # =====================================================
    # FAILOVER STREAM ROUTES
    # Used by dashboard template
    # =====================================================
    path(
        "stream/<uuid:uid>/",
        view_id_card,
        name="view_id_stream",
    ),

    path(
        "stream/<uuid:uid>/download/",
        download_id_stream,
        name="download_id_stream",
    ),
]
