import time
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
# SAFE IMAGE VALIDATION
# ======================================================
def validate_passport(file):
    errors = []

    if not file:
        errors.append("Passport photograph is required.")
        return errors

    if file.size == 0:
        errors.append("Uploaded file is empty.")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        errors.append("Only JPG or PNG images are allowed.")

    if file.size > MAX_FILE_MB * 1024 * 1024:
        errors.append("Passport file too large (max 5MB).")

    # Verify real image (not fake renamed file)
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)   # IMPORTANT: reset pointer after PIL read
    except Exception:
        errors.append("Invalid or corrupted image file.")

    return errors


# ======================================================
# SAFE CLOUDINARY SAVE WITH RETRY
# ======================================================
def save_passport(application, passport):

    last_error = None

    for attempt in range(UPLOAD_RETRIES):

        try:
            with transaction.atomic():

                # Remove old file (Cloudinary cleanup)
                if application.passport:
                    application.passport.delete(save=False)

                application.passport = passport
                application.save()

                # Verify persistence
                application.refresh_from_db()

                if not application.passport:
                    raise Exception("Passport not persisted")

                return True

        except Exception as e:
            last_error = e
            print(f"UPLOAD RETRY {attempt+1} FAILED:", str(e))
            time.sleep(1)

    raise last_error


# ======================================================
# APPLY FOR ID (BULLETPROOF)
# ======================================================
@login_required
def apply_for_id(request):

    student = get_object_or_404(Student, user=request.user)
    application = IDApplication.objects.filter(student=student).first()

    if request.method == "POST":

        passport = request.FILES.get("passport")

        # DEBUG (remove after confirmed working)
        print("FILES RECEIVED:", request.FILES)

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

                # Prevent editing after approval
                if application.status == IDApplication.STATUS_APPROVED:
                    messages.error(request, "Application already approved.")
                    return redirect("dashboard")

                save_passport(application, passport)

                # Reset review if re-upload
                if application.status != IDApplication.STATUS_PENDING:
                    application.status = IDApplication.STATUS_PENDING
                    application.reviewed_by = ""
                    application.save(update_fields=["status", "reviewed_by"])

        except Exception as e:
            print("FINAL UPLOAD FAILURE:", str(e))
            messages.error(request, "Passport upload failed. Try again.")
            return render(request, "apply.html", {"application": application})

        messages.success(request, "Passport uploaded successfully.")
        return redirect("dashboard")

    return render(request, "apply.html", {"application": application})


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

            generate_id_card(application)

    except Exception as e:
        print("ID GENERATION ERROR:", str(e))
        messages.error(request, "ID generation failed.")
        return redirect("admin_dashboard")

    messages.success(request, "Application approved and ID generated.")
    return redirect("admin_dashboard")
