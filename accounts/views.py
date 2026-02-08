from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from PIL import Image

from students.models import Student
from applications.models import IDApplication
from idcards.models import IDCard
from idcards.services import ensure_id_card_exists

from .forms import ForcePasswordChangeForm


# =========================
# HOME
# =========================
def home_view(request):
    return render(request, "home.html")


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:student_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            login(request, user)

            if getattr(user, "must_change_password", False):
                return redirect("accounts:force_change_password")

            return redirect("accounts:student_dashboard")

        messages.error(request, "Invalid login credentials")

    return render(request, "accounts/login.html")


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect("accounts:home")


# =========================
# STUDENT DASHBOARD
# =========================
@login_required
def student_dashboard(request):

    student = Student.objects.filter(user=request.user).first()

    if not student:
        messages.error(request, "Student profile not found. Contact admin.")
        return redirect("accounts:home")

    application = IDApplication.objects.filter(student=student).first()
    id_card = IDCard.objects.filter(student=student).first()

    # Auto-repair missing ID image
    if id_card and not id_card.image:
        try:
            ensure_id_card_exists(id_card)
            id_card.refresh_from_db()
        except Exception:
            pass

    issued = bool(id_card and id_card.image)

    timeline = {
        "applied": bool(application),
        "review": bool(application and application.status == IDApplication.STATUS_PENDING),
        "approved": bool(application and application.status == IDApplication.STATUS_APPROVED),
        "issued": issued,
    }

    return render(
        request,
        "accounts/student_dashboard.html",
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
    application = IDApplication.objects.filter(student=student).first()

    # -------------------------
    # POST — Upload passport
    # -------------------------
    if request.method == "POST":

        passport = request.FILES.get("passport")

        if not passport:
            messages.error(request, "Please select a passport photograph.")
            return redirect("accounts:apply")

        # Validate image safely
        try:
            img = Image.open(passport)
            img.verify()
            passport.seek(0)
        except Exception:
            messages.error(request, "Invalid or corrupted image file.")
            return redirect("accounts:apply")

        try:
            with transaction.atomic():

                if not application:
                    application = IDApplication.objects.create(student=student)

                if application.status == IDApplication.STATUS_APPROVED:
                    messages.error(request, "Application already approved.")
                    return redirect("accounts:student_dashboard")

                # Delete previous file (Cloudinary / storage safe)
                if application.passport:
                    application.passport.delete(save=False)

                application.passport = passport
                application.status = IDApplication.STATUS_PENDING
                application.reviewed_by = ""
                application.save()

        except Exception:
            messages.error(request, "Upload failed. Try again.")
            return redirect("accounts:apply")

        messages.success(request, "Passport uploaded successfully.")
        return redirect("accounts:student_dashboard")

    # -------------------------
    # GET — Show apply page
    # -------------------------
    return render(request, "applications/apply.html", {"application": application})


# =========================
# FORCE PASSWORD CHANGE
# =========================
@login_required
def force_change_password_view(request):

    user = request.user

    if not getattr(user, "must_change_password", False):
        return redirect("accounts:student_dashboard")

    if request.method == "POST":
        form = ForcePasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()

            user.must_change_password = False
            user.save(update_fields=["must_change_password"])

            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")

            return redirect("accounts:student_dashboard")
    else:
        form = ForcePasswordChangeForm(user)

    return render(request, "accounts/force_change_password.html", {"form": form})
