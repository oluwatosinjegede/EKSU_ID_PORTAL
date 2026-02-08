from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .services import ensure_id_card_exists
from applications.models import IDApplication


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, update_fields=None, **kwargs):
    """
    Self healing ID generator.

    Runs only when:
    - Image is missing
    - Approved application with passport exists
    - After database commit
    - Idempotent and safe
    """

    # Stop if image already exists
    image_field = getattr(instance, "image", None)
    if image_field and getattr(image_field, "name", None):
        return

    # Stop recursion when generator just saved image
    if update_fields and "image" in update_fields:
        return

    # Ensure approved application with passport exists
    application = IDApplication.objects.filter(
        student=instance.student,
        status=IDApplication.STATUS_APPROVED,
    ).only("id", "passport").first()

    if not application or not application.passport:
        return

    def _generate():
        try:
            ensure_id_card_exists(instance)
        except Exception:
            pass

    try:
        transaction.on_commit(_generate)
    except Exception:
        pass
