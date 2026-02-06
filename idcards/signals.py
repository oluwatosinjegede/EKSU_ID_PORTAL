from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import IDCard
from .generator import generate_id_card


@receiver(post_save, sender=IDCard)
def create_card_image(sender, instance, created, **kwargs):
    """
    Generate ID image ONLY when:
    - Passport exists
    - Image not already generated
    - Prevent recursive loops
    """

    # Must have passport
    if not instance.passport:
        return

    # Skip if image already exists (avoid regeneration loop)
    if instance.image:
        return

    try:
        # Run after DB commit (prevents recursion & race conditions)
        transaction.on_commit(lambda: generate_id_card(instance))
    except Exception:
        # Never crash due to signal
        pass
