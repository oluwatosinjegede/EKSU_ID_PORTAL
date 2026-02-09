from django.urls import path
from .views import verify_id, download_id, view_id_card, download_id_stream

app_name = "idcards"

urlpatterns = [

    # NEW secure URL (token required)
    path("verify/<uuid:uid>/<str:token>/", verify_id, name="verify_id_secure"),

    # LEGACY URL (no token ? still works)
    path("verify/<uuid:uid>/", verify_id, name="verify_id"),

    path(
        "verify/<uuid:uid>/<str:token>/download/",
        download_id,
        name="download_id",
    ),

    path("stream/<uuid:uid>/", view_id_card, name="view_id_stream"),
    path("stream/<uuid:uid>/download/", download_id_stream, name="download_id_stream"),
]
