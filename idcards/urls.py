from django.urls import path
from .views import verify_id

urlpatterns = [
    path("verify/<uuid:uid>/", verify_id, name="verify-id"),
]