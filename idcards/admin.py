from django.contrib import admin
from .models import IDCard


@admin.register(IDCard)
class IDCardAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "issued_at",
    )

    readonly_fields = (
        "issued_at",
    )
