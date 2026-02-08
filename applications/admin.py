from django.contrib import admin, messages
from django.db import transaction

from .models import IDApplication
from accounts.admin_mixins import RoleRestrictedAdminMixin
from idcards.models import IDCard
from idcards.generator import generate_id_card


# ======================================================
# BULK APPROVAL ACTION (SAFE + RELIABLE)
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

        # Skip already approved
        if application.status == IDApplication.STATUS_APPROVED:
            skipped += 1
            continue

        # Passport must exist
        if not application.passport:
            skipped += 1
            modeladmin.message_user(
                request,
                f"Skipped {application.student}: passport photo missing.",
                level=messages.WARNING,
            )
            continue

        try:
            with transaction.atomic():

                # Mark approved
                application.status = IDApplication.STATUS_APPROVED
                application.reviewed_by = request.user.get_username()
                application.save(update_fields=["status", "reviewed_by"])

                # Ensure IDCard exists
                card, _ = IDCard.objects.get_or_create(student=application.student)

                # Generate ID (idempotent)
                if not card.image:
                    generate_id_card(card)

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
# ADMIN CONFIG (CRASH-SAFE)
# ======================================================
@admin.register(IDApplication)
class IDApplicationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):

    allowed_roles = ["ADMIN", "REVIEWER", "APPROVER"]

    list_display = (
        "student",
        "status",
        "created_at",
    )

    list_filter = ("status",)

    search_fields = (
        "student__matric_number",
        "student__first_name",
        "student__last_name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "reviewed_by",
    )

    fields = (
        "student",
        "passport",
        "status",
        "reviewed_by",
        "created_at",
    )

    actions = [approve_application]

    # --------------------------------------------------
    # Guarantee ID generation even when admin edits manually
    # --------------------------------------------------
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == IDApplication.STATUS_APPROVED and obj.passport:
            try:
                card, _ = IDCard.objects.get_or_create(student=obj.student)
                if not card.image:
                    generate_id_card(card)
            except Exception:
                pass
