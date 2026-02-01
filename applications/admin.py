from django.contrib import admin, messages
from .models import IDApplication
from accounts.admin_mixins import RoleRestrictedAdminMixin


@admin.action(description="Approve application")
def approve_application(modeladmin, request, queryset):
    user_role = getattr(request.user, "role", None)

    if user_role not in ["ADMIN", "APPROVER"]:
        modeladmin.message_user(
            request,
            "You do not have permission to approve applications.",
            level=messages.ERROR,
        )
        return

    updated = 0

    for application in queryset:
        if application.status == "APPROVED":
            continue

        application.status = "APPROVED"
        application.reviewed_by = request.user.get_username()
        application.save(update_fields=["status", "reviewed_by"])

        updated += 1

    modeladmin.message_user(
        request,
        f"{updated} application(s) approved. ID cards issued automatically.",
        level=messages.SUCCESS,
    )


@admin.register(IDApplication)
class IDApplicationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = ["ADMIN", "REVIEWER", "APPROVER"]

    list_display = ("student", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("created_at",)
    actions = [approve_application]
