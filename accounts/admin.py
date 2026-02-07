from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as AuthUser


# =====================================================
# SAFELY UNREGISTER DEFAULT DJANGO USER
# =====================================================
try:
    admin.site.unregister(AuthUser)
except admin.sites.NotRegistered:
    pass


# =====================================================
# CUSTOM USER MODEL
# =====================================================
User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # =========================
    # LIST VIEW
    # =========================
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
        "is_superuser",
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # =========================
    # FIELD GROUPS (EDIT USER)
    # =========================
    fieldsets = (
        (None, {"fields": ("username", "password")}),

        ("Personal Info", {
            "fields": ("first_name", "last_name", "email")
        }),

        ("Permissions", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Security", {
            "fields": ("must_change_password",)
        }),

        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    # =========================
    # ADD USER FORM
    # =========================
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "first_name",
                "last_name",
                "role",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )
