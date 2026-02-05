from django.contrib import admin
from django.utils.html import format_html
from .models import IDCard


@admin.register(IDCard)
class IDCardAdmin(admin.ModelAdmin):
    list_display = ("student", "image_preview")

    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if not obj.image:
            return "No ID card generated"
        return format_html(
            '<img src="{}" style="max-width:300px; border:1px solid #ccc;" />',
            obj.image.url,
        )

    image_preview.short_description = "ID Card Preview"
