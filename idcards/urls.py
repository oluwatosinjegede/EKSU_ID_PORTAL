from django.urls import path
from .views import verify_id, download_id

urlpatterns = [
    # QR verification (opens ID image)
    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    # Optional: force download instead of open
    path("verify/<uuid:uid>/download/", download_id, name="download_id"),
]
