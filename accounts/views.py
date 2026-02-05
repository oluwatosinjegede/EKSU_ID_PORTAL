from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from students.models import Student
from applications.models import IDApplication
from idcards.models import IDCard


# =========================
# HOME
# =========================
def home_view(request):
    return render(request, "home.html")


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if getattr(user, "must_change_password", False):
                return redirect("force-change-password")

            if hasattr(user, "student"):
                return redirect("student-dashboard")

            return redirect("/admin/")

        return render(
            request,
            "auth/login.html",
            {"error": "Invalid login credentials"},
        )

    return render(request, "auth/login.html")


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("home")


# =========================
# STUDENT DASHBOARD
# =========================
@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)

    application = (
        IDApplication.objects.filter(student=student)
        .select_related()
        .first()
    )

    id_card = IDCard.objects.filter(student=student).first()

    # Safe check for image-based ID
    issued = bool(id_card and getattr(id_card, "image", None))

    timeline = {
        "applied": bool(application),
        "review": bool(application and application.status == IDApplication.STATUS_PENDING),
        "approved": bool(application and application.status == IDApplication.STATUS_APPROVED),
        "issued": issued,
    }

    return render(
        request,
        "student/dashboard.html",
        {
            "student": student,
            "application": application,
            "id_card": id_card,
            "timeline": timeline,
            "issued": issued,
        },
    )


# =========================
# APPLY FOR ID
# =========================
@login_required
def apply_id_view(request):
    student = get_object_or_404(Student, user=request.user)

    # Prevent duplicate application
    if IDApplication.objects.filter(student=student).exists():
        return redirect("student-dashboard")

    if request.method == "POST":
        passport = request.FILES.get("passport")
        signature = request.FILES.get("signature")

        if not passport or not signature:
            return render(
                request,
                "student/apply_id.html",
                {"error": "Passport and signature are required"},
            )

        IDApplication.objects.create(
            student=student,
            passport=passport,
            signature=signature,
        )

        return redirect("student-dashboard")

    return render(request, "student/apply_id.html")


# =========================
# FORCE PASSWORD CHANGE
# =========================
@login_required
def force_change_password_view(request):
    user = request.user

    if not getattr(user, "must_change_password", False):
        return redirect("student-dashboard")

    if request.method == "POST":
        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        if not p1 or not p2:
            return render(
                request,
                "auth/force_change_password.html",
                {"error": "All fields are required"},
            )

        if p1 != p2:
            return render(
                request,
                "auth/force_change_password.html",
                {"error": "Passwords do not match"},
            )

        if len(p1) < 8:
            return render(
                request,
                "auth/force_change_password.html",
                {"error": "Password must be at least 8 characters long"},
            )

        user.set_password(p1)
        user.must_change_password = False
        user.save()

        update_session_auth_hash(request, user)

        return redirect("student-dashboard")

    return render(request, "auth/force_change_password.html")
