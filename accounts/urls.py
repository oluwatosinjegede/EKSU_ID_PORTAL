from django.urls import path
from .views import (
    home_view,
    login_view,
    logout_view,
    student_dashboard,
    apply_id_view,
    force_change_password_view,
)

app_name = "accounts"

urlpatterns = [
    # =========================
    # PUBLIC
    # =========================
    path("", home_view, name="home"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # =========================
    # STUDENT
    # =========================
    path("student/dashboard/", student_dashboard, name="student-dashboard"),
    path("student/apply/", apply_id_view, name="student-apply"),

    # =========================
    # SECURITY
    # =========================
    path("change-password/", force_change_password_view, name="force-change-password"),
]
