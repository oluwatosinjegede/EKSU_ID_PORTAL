from django.urls import path
from .views import apply_for_id, approve_id

app_name = "applications"   # Enables namespace (applications:*)

urlpatterns = [
    # -------------------------------------------------
    # STUDENT — Apply for ID
    # -------------------------------------------------
    path(
        "student/apply/",
        apply_for_id,
        name="apply_id",
    ),

    # -------------------------------------------------
    # ADMIN — Approve ID
    # -------------------------------------------------
    path(
        "admin/approve/<int:app_id>/",
        approve_id,
        name="approve_id",
    ),
]
