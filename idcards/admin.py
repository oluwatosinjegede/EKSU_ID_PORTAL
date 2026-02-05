from django.contrib import admin
from django.utils.html import format_html
from .models import IDCard


@admin.register(IDCard)
class IDCardAdmin(admin.ModelAdmin):
    list_display = ("student", "has_image", "image_preview")
    readonly_fields = ("image_preview",)

    # -----------------------------------
    # Show YES/NO if ID card exists
    # -----------------------------------
    def has_image(self, obj):
        image_field = getattr(obj, "image", None)
        return bool(image_field and getattr(image_field, "name", None))

    has_image.boolean = True
    has_image.short_description = "Generated"

    # -----------------------------------
    # Safe Image Preview
    # -----------------------------------
    def image_preview(self, obj):
        image_field = getattr(obj, "image", None)

        if not image_field or not getattr(image_field, "url", None):
            return "No ID card generated"

        return format_html(
            '<img src="{}" style="max-width:320px; border:1px solid #ccc; border-radius:6px;" />',
            image_field.url,
        )

    image_preview.short_description = "ID Card Preview"
