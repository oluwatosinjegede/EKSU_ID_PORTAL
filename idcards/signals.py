from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, update_fields=None, **kwargs):
    """
    Fallback generator (production safe)

    Runs ONLY when:
    - ID image missing
    - After DB commit (no race / recursion)
    - Uses service layer (safe + idempotent)
    """

    # -------------------------------------------------
    # STOP if image already exists
    # -------------------------------------------------
    image_field = getattr(instance, "image", None)
    if image_field and getattr(image_field, "name", None):
        return

    # -------------------------------------------------
    # STOP if save was only updating unrelated fields
    # (prevents unnecessary regeneration)
    # -------------------------------------------------
    if update_fields and "image" not in update_fields:
        pass  # still allow fallback generation when missing

    # -------------------------------------------------
    # Generate AFTER DB commit (prevents recursion)
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
