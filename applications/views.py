from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import IDApplication
from students.models import Student
from idcards.utils import generate_id_card


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


@login_required
def apply_for_id(request):
    student = get_object_or_404(Student, user=request.user)

    if request.method == "POST":
        passport = request.FILES.get("passport")
        signature = request.FILES.get("signature")

        # ---- validation ----
        errors = []

        if not passport:
            errors.append("Passport photograph is required.")

        if not signature:
            errors.append("Signature image is required.")

        if passport and passport.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append("Passport must be a JPG or PNG image.")

        if signature and signature.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append("Signature must be a JPG or PNG image.")

        if errors:
            return render(
                request,
                "apply.html",
                {"errors": errors},
            )

        # ---- atomic create (prevents partial saves) ----
        with transaction.atomic():
            IDApplication.objects.create(
                student=student,
                passport=passport,
                signature=signature,
            )

        return redirect("dashboard")

    return render(request, "apply.html")


@login_required
def approve_id(request, app_id):
    application = get_object_or_404(IDApplication, id=app_id)

    # prevent double-approval
    if application.status == "APPROVED":
        return redirect("admin_dashboard")

    with transaction.atomic():
        application.status = "APPROVED"
        application.reviewed_by = request.user.username
        application.save(update_fields=["status", "reviewed_by"])

        # idempotent card generation (must use get_or_create internally)
        generate_id_card(application)

    return redirect("admin_dashboard")
