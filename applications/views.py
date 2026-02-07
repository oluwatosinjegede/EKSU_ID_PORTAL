import time
import traceback
from PIL import Image

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from .models import IDApplication
from students.models import Student
from idcards.utils import generate_id_card


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_MB = 5
UPLOAD_RETRIES = 3


# ======================================================
# VALIDATE PASSPORT IMAGE (SAFE)
# ======================================================
def validate_passport(file):
    if not file:
        return ["Passport photograph is required."]

    errors = []

    if file.size == 0:
        errors.append("Uploaded file is empty.")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        errors.append("Only JPG or PNG images are allowed.")

    if file.size > MAX_FILE_MB * 1024 * 1024:
        errors.append("Passport file too large (max 5MB).")

    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        errors.append("Invalid or corrupted image file.")

    return errors


# ======================================================
# SAVE PASSPORT WITH RETRY (CLOUDINARY SAFE)
# ======================================================
def save_passport(application, passport):

    last_error = None

    for attempt in range(UPLOAD_RETRIES):
        try:
            if application.passport:
                application.passport.delete(save=False)

            application.passport = passport
            application.save()
            application.refresh_from_db()

            if not application.passport:
                raise RuntimeError("Passport not persisted")

            return True

        except Exception as e:
            last_error = e
            print(f"[UPLOAD RETRY {attempt+1}] {str(e)}")
            time.sleep(1)

    raise last_error


# ======================================================
# APPLY FOR ID
# ======================================================
@login_required
def apply_for_id(request):

    student = get_object_or_404(Student, user=request.user)
    application = IDApplication.objects.filter(student=student).first()

    if request.method == "POST":

        passport = request.FILES.get("passport")

        # ---------- FILE ARRIVAL CHECK ----------
        if not passport:
            messages.error(request, "No file received by server.")
            return redirect("accounts:apply_id")

        # ---------- VALIDATION ----------
        errors = validate_passport(passport)
        if errors:
            return render(
                request,
                "apply.html",
                {"errors": errors, "application": application},
            )

        # ---------- SAVE ----------
        try:
            with transaction.atomic():

                if not application:
                    application = IDApplication.objects.create(student=student)

                if application.status == IDApplication.STATUS_APPROVED:
                    messages.error(request, "Application already approved.")
                    return redirect("accounts:student_dashboard")

                save_passport(application, passport)

                application.status = IDApplication.STATUS_PENDING
                application.reviewed_by = ""
                application.save(update_fields=["status", "reviewed_by"])

        except Exception as e:
            print("==== UPLOAD FAILURE ====")
            print("ERROR:", str(e))
            traceback.print_exc()
            print("========================")

            messages.error(request, "Passport upload failed.")
            return redirect("accounts:apply_id")

        messages.success(request, "Passport uploaded successfully.")
        return redirect("accounts:student_dashboard")

    return render(request, "accounts/apply.html", {"application": application})


# ======================================================
# APPROVE ID (SAFE + IDEMPOTENT)
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

            generate_id_card(application)

    except Exception as e:
        print("[ID GENERATION ERROR]", str(e))
        traceback.print_exc()
        messages.error(request, "ID generation failed.")
        return redirect("admin_dashboard")

    messages.success(request, "Application approved and ID generated.")
    return redirect("admin_dashboard")
