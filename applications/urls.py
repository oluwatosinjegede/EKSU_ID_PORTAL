from django.urls import path
from .views import apply_for_id, approve_id

urlpatterns = [
    path("student/apply/", apply_for_id, name="student_apply"),
    path("admin/approve/<int:app_id>/", approve_id, name="approve_id"),
]
