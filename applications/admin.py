from django.contrib import admin, messages
from django.db import transaction

from .models import IDApplication
from accounts.admin_mixins import RoleRestrictedAdminMixin
from idcards.models import IDCard
from idcards.services import generate_id_card


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
    failed = 0

    for application in queryset:

        # Skip already approved
        if application.status == "APPROVED":
            continue

        # Passport must exist
        if not application.passport:
            modeladmin.message_user(
                request,
                f"Skipped {application.student}: passport photo missing.",
                level=messages.WARNING,
            )
            continue

        try:
            with transaction.atomic():

                # Mark approved
                application.status = "APPROVED"
                application.reviewed_by = request.user.get_username()
                application.save(update_fields=["status", "reviewed_by"])

                # Ensure IDCard exists
                idcard, _ = IDCard.objects.get_or_create(student=application.student)

                # Generate ID card (Cloudinary-safe)
                generate_id_card(idcard)

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
        f"{approved} approved, {failed} failed. ID cards generated automatically.",
        level=messages.SUCCESS,
    )


@admin.register(IDApplication)
class IDApplicationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = ["ADMIN", "REVIEWER", "APPROVER"]

    list_display = ("student", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)

    # Only passport required — no signature
    fields = ("student", "passport", "status", "created_at")

    actions = [approve_application]
