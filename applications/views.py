from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import IDApplication
from students.models import Student
from idcards.utils import generate_id_card


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


# ======================================================
# APPLY FOR ID  (PASSPORT ONLY)
# ======================================================
@login_required
def apply_for_id(request):
    student = get_object_or_404(Student, user=request.user)

    # Prevent duplicate applications
    existing_app = IDApplication.objects.filter(student=student).first()

    if request.method == "POST":
        passport = request.FILES.get("passport")

        errors = []

        # -------- Validation --------
        if not passport:
            errors.append("Passport photograph is required.")

        if passport and passport.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append("Passport must be a JPG or PNG image.")

        if errors:
            return render(
                request,
                "apply.html",
                {
                    "errors": errors,
                    "application": existing_app,
                },
            )

        # -------- Atomic save (Railway safe) --------
        with transaction.atomic():

            if existing_app:
                # Replace passport if re-uploading
                existing_app.passport = passport
                existing_app.status = IDApplication.STATUS_PENDING
                existing_app.reviewed_by = ""
                existing_app.save(update_fields=["passport", "status", "reviewed_by"])
            else:
                IDApplication.objects.create(
                    student=student,
                    passport=passport,
                )

        return redirect("dashboard")

    return render(
        request,
        "apply.html",
        {
            "application": existing_app,
        },
    )


# ======================================================
# APPROVE ID  (AUTO GENERATE CARD)
# ======================================================
@login_required
def approve_id(request, app_id):
    application = get_object_or_404(IDApplication, id=app_id)

    if application.status == IDApplication.STATUS_APPROVED:
        return redirect("admin_dashboard")

    with transaction.atomic():
        application.status = IDApplication.STATUS_APPROVED
        application.reviewed_by = request.user.username
        application.save(update_fields=["status", "reviewed_by"])

        # Safe / idempotent generator
        generate_id_card(application)

    return redirect("admin_dashboard")
