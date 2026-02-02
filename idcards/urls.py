from django.urls import path
from .views import verify_id
from . import views

urlpatterns = [
#    path("verify/<uuid:uid>/", verify_id, name="verify-id"),
    path("verify/<int:pk>/", views.verify_id_card, name="verify-id-card"),
]