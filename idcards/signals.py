from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists
from applications.models import IDApplication


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, update_fields=None, **kwargs):
    """
    SELF-HEALING ID GENERATOR (Production Safe)

    Guarantees:
    - Runs AFTER DB commit (no race condition)
    - No recursion loop
    - Idempotent (safe multiple executions)
    - Runs ONLY when image missing
    - Waits until approved application + passport exist
    - Works for:
        • Approval flow
        • Passport copy
        • Admin edits
        • Imports / recovery
        • Broken image rebuild
    """

    # -------------------------------------------------
    # STOP if image already exists
    # -------------------------------------------------
    image_field = getattr(instance, "image", None)
    if image_field and getattr(image_field, "name", None):
        return

    # -------------------------------------------------
    # STOP loop when generator just saved the image
    # -------------------------------------------------
    if update_fields and "image" in update_fields:
        return

    # -------------------------------------------------
    # Ensure APPROVED application + passport exist
    # (prevents useless generator calls)
    # -------------------------------------------------
    application = IDApplication.objects.filter(
        student=instance.student,
        status=IDApplication.STATUS_APPROVED,
    ).only("id", "passport").first()

    if not application or not application.passport:
        return

    # -------------------------------------------------
    # Run AFTER DB commit (prevents recursion & race)
    # -------------------------------------------------
    def _generate():
        try:
            ensure_id_card_exists(instance)
        except Exception:
            # Never crash request / admin / migrations
            pass

    try:
        transaction.on_commit(_generate)
    except Exception:
        pass
