from django.contrib import admin, messages
from django.db import transaction

from .models import IDApplication
from accounts.admin_mixins import RoleRestrictedAdminMixin
from idcards.services import generate_id_card   # ? SERVICE (NOT generator)


# ======================================================
# BULK APPROVAL ACTION — PRODUCTION SAFE
# ======================================================
@admin.action(description="Approve application and generate ID card")
def approve_application(modeladmin, request, queryset):

    user_role = getattr(request.user, "role", None)

    if user_role not in ["ADMIN", "APPROVER"]:
        modeladmin.message_user(
            request,
            "You do not have permission to approve applications.",
            level=messages.ERROR,
        )
        return

    approved = 0
    skipped = 0
    failed = 0

    for application in queryset.select_related("student"):

        # Already approved
        if application.status == IDApplication.STATUS_APPROVED:
            skipped += 1
            continue

        # Passport required
        if not application.passport:
            skipped += 1
            modeladmin.message_user(
                request,
                f"Skipped {application.student}: passport missing.",
                level=messages.WARNING,
            )
            continue

        try:
            with transaction.atomic():

                # Approve
                application.status = IDApplication.STATUS_APPROVED
                application.reviewed_by = request.user.get_username()
                application.save(update_fields=["status", "reviewed_by"])

                # Generate ID via SERVICE (safe, idempotent)
                generate_id_card(application)

                approved += 1

        except Exception as e:
            failed += 1
            modeladmin.message_user(
                request,
                f"Failed for {application.student}: {str(e)}",
                level=messages.ERROR,
            )

    modeladmin.message_user(
        request,
        f"{approved} approved, {skipped} skipped, {failed} failed.",
        level=messages.SUCCESS,
    )


# ======================================================
# ADMIN CONFIG — SAFE
# ======================================================
@admin.register(IDApplication)
class IDApplicationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):

    allowed_roles = ["ADMIN", "REVIEWER", "APPROVER"]

    list_display = ("student", "status", "created_at")
    list_filter = ("status",)

    search_fields = (
        "student__matric_number",
        "student__first_name",
        "student__last_name",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "reviewed_by")

    fields = (
        "student",
        "passport",
        "status",
        "reviewed_by",
        "created_at",
    )

    actions = [approve_application]

    # --------------------------------------------------
    # Ensure ID generation when admin edits manually
    # --------------------------------------------------
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == IDApplication.STATUS_APPROVED and obj.passport:
            try:
                generate_id_card(obj)   # ? SERVICE
            except Exception:
                pass
