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
    application = IDApplication.objects.filter(student=student).first()

    if request.method == "POST":

        passport = request.FILES.get("passport")

        # DEBUG (REMOVE AFTER FIXED)
        print("FILES RECEIVED:", request.FILES)

        errors = []

        # ---------- VALIDATION ----------
        if not passport:
            errors.append("Passport photograph is required.")
        else:
            if passport.size == 0:
                errors.append("Uploaded file is empty.")

            if passport.content_type not in ALLOWED_IMAGE_TYPES:
                errors.append("Only JPG or PNG images are allowed.")

            if passport.size > MAX_FILE_MB * 1024 * 1024:
                errors.append("Passport file too large (max 5MB).")

        if errors:
            return render(
                request,
                "apply.html",
                {"errors": errors, "application": application},
            )

        # ---------- SAVE (Cloudinary Safe) ----------
        try:
            with transaction.atomic():

                if application:

                    if application.status == IDApplication.STATUS_APPROVED:
                        messages.error(request, "Application already approved.")
                        return redirect("dashboard")

                    # DELETE OLD FILE FROM CLOUDINARY (optional but recommended)
                    if application.passport:
                        application.passport.delete(save=False)

                    # IMPORTANT: assign then force save
                    application.passport = passport
                    application.status = IDApplication.STATUS_PENDING
                    application.reviewed_by = ""

                    application.save()   # <-- MUST be full save

                else:
                    application = IDApplication.objects.create(
                        student=student,
                        passport=passport,
                    )

                # ---------- VERIFY SAVE ----------
                application.refresh_from_db()

                if not application.passport:
                    raise Exception("Passport did not persist after save")

        except Exception as e:
            print("UPLOAD ERROR:", str(e))
            messages.error(request, "Passport upload failed. Check server logs.")
            return render(
                request,
                "apply.html",
                {"application": application},
            )

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

    messages.success(request, "Application approved and ID card generated.")
    return redirect("admin_dashboard")
