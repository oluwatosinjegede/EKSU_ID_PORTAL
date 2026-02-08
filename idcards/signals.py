from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, update_fields=None, **kwargs):
    """
    SELF-HEALING ID GENERATOR (Production Safe)

    Guarantees:
    - Runs AFTER DB commit (no race condition)
    - No recursion
    - Idempotent (safe to run multiple times)
    - Only runs when image missing
    - Works for:
        • Approval flow
        • Passport copy
        • Admin edits
        • Imports
        • Recovery of broken cards
    """

    # -------------------------------------------------
    # STOP if image already exists
    # -------------------------------------------------
    image_field = getattr(instance, "image", None)
    if image_field and getattr(image_field, "name", None):
        return

    # -------------------------------------------------
    # STOP if save explicitly updated image only
    # (prevents loop when generator saves image)
    # -------------------------------------------------
    if update_fields and "image" in update_fields:
        return

    # -------------------------------------------------
    # Run AFTER DB COMMIT (prevents recursion + race)
    # -------------------------------------------------
    def _generate():
        try:
            ensure_id_card_exists(instance)
        except Exception:
            # Never crash request / admin / migration
            pass

    try:
        transaction.on_commit(_generate)
    except Exception:
        pass
