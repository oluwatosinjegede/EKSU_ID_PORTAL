from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .generator import generate_id_card


@receiver(post_save, sender=IDCard)
def ensure_card_image(sender, instance, created, **kwargs):
    """
    Fallback generator:
    Runs only if image missing.
    Prevents recursion.
    """

    if instance.image:
        return

    try:
        transaction.on_commit(lambda: generate_id_card(instance))
    except Exception:
        pass
