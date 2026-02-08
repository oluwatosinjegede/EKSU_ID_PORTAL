from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, **kwargs):
    """
    Fallback generator — production safe

    Runs ONLY when:
    - ID image missing
    - Approved application exists
    - Passport exists
    - After DB commit (no race condition)

    Uses service layer (not raw generator)
    """

    # Already generated ? stop
    if instance.image and getattr(instance.image, "name", None):
        return

    def _generate():
        try:
            ensure_id_card_exists(instance)
        except Exception:
            # Never crash request or admin save
            pass

    try:
        # Run AFTER DB commit ? prevents race conditions
        transaction.on_commit(_generate)
    except Exception:
        pass
