from django.contrib import admin, messages
from django.utils.html import format_html
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists


@admin.register(IDCard)
class IDCardAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "status",
        "has_image",
        "image_preview_small",
    )

    readonly_fields = (
        "image_preview",
        "uid",
        "created_at",
    )

    search_fields = (
        "student__matric_number",
        "student__first_name",
        "student__last_name",
    )

    list_filter = ("created_at",)

    actions = ["regenerate_id_cards"]

    # =====================================================
    # STATUS COLUMN
    # =====================================================
    def status(self, obj):
        image_field = getattr(obj, "image", None)
        if image_field and getattr(image_field, "name", None):
            return "READY"
        return "MISSING"

    status.short_description = "Status"

    # =====================================================
    # HAS IMAGE BOOLEAN
    # =====================================================
    def has_image(self, obj):
        image_field = getattr(obj, "image", None)
        return bool(image_field and getattr(image_field, "name", None))

    has_image.boolean = True
    has_image.short_description = "Generated"

    # =====================================================
    # SMALL PREVIEW (LIST VIEW SAFE)
    # =====================================================
    def image_preview_small(self, obj):
        image_field = getattr(obj, "image", None)

        if not image_field or not getattr(image_field, "url", None):
            return "-"   # SAFE ASCII (avoid encoding crash)

        return format_html(
            '<img src="{}" style="height:60px; border-radius:4px;" />',
            image_field.url,
        )

    image_preview_small.short_description = "Preview"

    # =====================================================
    # FULL PREVIEW (DETAIL VIEW)
    # =====================================================
    def image_preview(self, obj):
        image_field = getattr(obj, "image", None)

        if not image_field or not getattr(image_field, "url", None):
            return "No ID card generated"

        return format_html(
            '<img src="{}" style="max-width:420px; border:1px solid #ccc; border-radius:8px;" />',
            image_field.url,
        )

    image_preview.short_description = "ID Card Preview"

    # =====================================================
    # BULK REGENERATE ACTION (SELF-HEAL SAFE)
    # =====================================================
    @admin.action(description="Regenerate selected ID cards")
    def regenerate_id_cards(self, request, queryset):

        regenerated = 0
        skipped = 0
        failed = 0

        for card in queryset.select_related("student"):
            try:
                with transaction.atomic():

                    result = ensure_id_card_exists(card)

                    if result:
                        regenerated += 1
                    else:
                        skipped += 1

            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"Failed for {card.student}: {str(e)}",
                    level=messages.ERROR,
                )

        self.message_user(
            request,
            f"{regenerated} regenerated, {skipped} skipped, {failed} failed.",
            level=messages.SUCCESS,
        )
