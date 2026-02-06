from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from .models import IDApplication
from students.models import Student
from idcards.utils import generate_id_card


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_MB = 5


# ======================================================
# APPLY FOR ID  (PASSPORT ONLY)
# ======================================================
@login_required
def apply_for_id(request):
    student = get_object_or_404(Student, user=request.user)

    existing_app = IDApplication.objects.filter(student=student).first()

    if request.method == "POST":
        passport = request.FILES.get("passport")

        # ---- DEBUG (remove after confirmed working) ----
        print("FILES RECEIVED:", request.FILES)

        errors = []

        # -------- Validation --------
        if not passport:
            errors.append("Passport photograph is required.")
        else:
            if passport.content_type not in ALLOWED_IMAGE_TYPES:
                errors.append("Passport must be JPG or PNG.")

            if passport.size > MAX_FILE_MB * 1024 * 1024:
                errors.append("Passport file too large (max 5MB).")

        if errors:
            return render(
                request,
                "apply.html",
                {
                    "errors": errors,
                    "application": existing_app,
                },
            )

        # -------- Atomic save --------
        try:
            with transaction.atomic():

                if existing_app:
                    # Optional: prevent change after approval
                    if existing_app.status == IDApplication.STATUS_APPROVED:
                        messages.error(request, "Application already approved.")
                        return redirect("dashboard")

                    existing_app.passport = passport
                    existing_app.status = IDApplication.STATUS_PENDING
                    existing_app.reviewed_by = ""
                    existing_app.save(
                        update_fields=["passport", "status", "reviewed_by"]
                    )

                else:
                    IDApplication.objects.create(
                        student=student,
                        passport=passport,
                    )

        except Exception as e:
            print("UPLOAD ERROR:", e)
            messages.error(request, "Passport upload failed. Try again.")
            return redirect("dashboard")

        messages.success(request, "Passport uploaded successfully.")
        return redirect("dashboard")

    return render(
        request,
        "apply.html",
        {"application": existing_app},
    )


# ======================================================
# APPROVE ID  (AUTO GENERATE CARD)
# ======================================================
@login_required
def approve_id(request, app_id):
    application = get_object_or_404(IDApplication, id=app_id)

    if application.status == IDApplication.STATUS_APPROVED:
        messages.info(request, "Application already approved.")
        return redirect("admin_dashboard")

    try:
        with transaction.atomic():
            application.status = IDApplication.STATUS_APPROVED
            application.reviewed_by = request.user.username
            application.save(update_fields=["status", "reviewed_by"])

            # Generate ID card safely
            generate_id_card(application)

    except Exception as e:
        print("ID GENERATION ERROR:", e)
        messages.error(request, "ID generation failed.")
        return redirect("admin_dashboard")

    messages.success(request, "Application approved and ID generated.")
    return redirect("admin_dashboard")
